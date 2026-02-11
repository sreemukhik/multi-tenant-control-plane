import kopf
import asyncio
import structlog
import secrets
import datetime
import uuid
from sqlalchemy import select
from app.models import Store, AuditLog
from app.database import AsyncSessionLocal
from app.services.helm import helm_install, helm_uninstall
from app.services.kubernetes import delete_namespace
from app.config import settings

logger = structlog.get_logger()

# Helper to run kubectl commands
async def run_kubectl(args, container=None, namespace=None):
    cmd = ["kubectl"]
    if namespace:
        cmd.extend(["-n", namespace])
    cmd.extend(args)
    
    proc = await asyncio.create_subprocess_exec(
        *cmd, 
        stdout=asyncio.subprocess.PIPE, 
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    output = stdout.decode().strip()
    
    # Filter out common noisy warnings
    noise = ["Defaulted container", "Defaulting to user 'root'"]
    lines = [l for l in output.splitlines() if not any(n in l for n in noise)]
    clean_output = "\n".join(lines).strip()

    if proc.returncode != 0:
        raise Exception(stderr.decode() or clean_output)
    return clean_output
import yaml

# Hardening Templates
RESOURCE_QUOTA_TEMPLATE = """
apiVersion: v1
kind: ResourceQuota
metadata:
  name: store-quota
  namespace: {namespace}
spec:
  hard:
    requests.cpu: "200m"
    requests.memory: "512Mi"
    limits.cpu: "1"
    limits.memory: "1Gi"
    pods: "10"
    services: "5"
    persistentvolumeclaims: "5"
"""

NETWORK_POLICY_TEMPLATE = """
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: store-isolation
  namespace: {namespace}
spec:
  podSelector: {{}}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: {namespace}
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: urumi-platform
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: {namespace}
  - to:
    - ports:
      - port: 53
        protocol: UDP
      - port: 53
        protocol: TCP
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 10.0.0.0/8
        - 172.16.0.0/12
        - 192.168.0.0/16
"""

async def apply_hardening(namespace: str):
    """
    Apply ResourceQuota and NetworkPolicy to the store namespace.
    """
    quota_yaml = RESOURCE_QUOTA_TEMPLATE.format(namespace=namespace)
    netpol_yaml = NETWORK_POLICY_TEMPLATE.format(namespace=namespace)
    
    for manifest in [quota_yaml, netpol_yaml]:
        try:
            # Use kubectl apply to ensure idempotency
            await run_command_async(["kubectl", "apply", "-f", "-"], input_str=manifest)
        except Exception as e:
            logger.error("hardening_apply_failed", namespace=namespace, error=str(e))

async def run_command_async(cmd, input_str=None):
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE if input_str else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate(input=input_str.encode() if input_str else None)
    if process.returncode != 0:
        raise Exception(f"Command failed: {stderr.decode()}")
    return stdout.decode()
@kopf.on.create('stores.urumi.io')
@kopf.on.resume('stores.urumi.io')
async def create_store(spec, name, meta, status, **kwargs):
    """
    Operator Handler: Provision a new store.
    """
    namespace = name
    store_id_str = meta.get('labels', {}).get('store_id')
    
    logger.info("operator_create_event", store=name, store_id=store_id_str)
    
    async with AsyncSessionLocal() as db:
        store = None
        if store_id_str:
            stmt = select(Store).where(Store.id == uuid.UUID(store_id_str))
            result = await db.execute(stmt)
            store = result.scalars().first()
        
        if store and store.status == "ready":
            logger.info("operator_skip_ready", store=name)
            return {"phase": "Ready", "message": "Already provisioned"}
            
        async def log_step(action, metadata=None):
            if not store: return
            try:
                log = AuditLog(
                    action=action, 
                    resource_type="store", 
                    resource_id=str(store.id), 
                    metadata_=metadata or {}
                )
                db.add(log)
                await db.commit()
            except: pass

        if store:
            store.status = "provisioning"
            store.provisioning_started_at = datetime.datetime.now(datetime.timezone.utc)
            await db.commit()
            await log_step("operator.provision_started", {"crd_name": name})

        try:
            engine = spec.get('engine', 'woocommerce')
            base_domain = "127.0.0.1.nip.io"
            
            db_password = spec.get('dbPassword')
            root_password = spec.get('adminPassword')
            wp_password = spec.get('adminPassword')
            
            if not wp_password or not db_password:
                logger.error("missing_spec_passwords", store=name)
                raise Exception("Passwords missing from Store spec")
            
            chart_path = "oci://registry-1.docker.io/bitnamicharts/wordpress"
            release_name = name
            
            values = {
                 "wordpressUsername": spec.get('adminUser', 'admin'),
                 "wordpressPassword": wp_password,
                 "wordpressEmail": f"admin@{namespace}.local",
                 "wordpressBlogName": spec.get('name', 'My Store'),
                 "service.type": "ClusterIP",
                 "ingress.enabled": "true",
                 "ingress.ingressClassName": "traefik",
                 "ingress.hostname": f"{namespace}.{base_domain}",
                 "mariadb.enabled": "true",
                 "mariadb.auth.rootPassword": root_password,
                 "mariadb.auth.password": db_password,
                 "mariadb.primary.persistence.enabled": "true",
                 "mariadb.primary.persistence.size": "1Gi",
                 "mysql.enabled": "false",
                 "resources.requests.cpu": "50m",
                 "resources.requests.memory": "128Mi",
                 "resources.limits.memory": "512Mi",
                 "mariadb.primary.resources.requests.cpu": "50m",
                 "mariadb.primary.resources.requests.memory": "128Mi",
                 "mariadb.primary.resources.limits.memory": "256Mi",
            }
            
            await log_step("operator.helm_install")
            await helm_install(
                release_name=release_name,
                chart_path=chart_path,
                namespace=namespace,
                values=values,
                timeout=f"{settings.PROVISIONING_TIMEOUT_MINUTES}m",
                wait=True,
                create_namespace=True
            )

            # Apply Expert Hardening
            await log_step("operator.applying_hardening")
            await apply_hardening(namespace)
            
            if engine == "woocommerce":
                await log_step("operator.configure_woocommerce")
                
                pod_name = ""
                for _ in range(40):
                    try:
                        pod_name = await run_kubectl(["get", "pods", "-n", namespace, "-l", "app.kubernetes.io/name=wordpress", "-o", "jsonpath={.items[0].metadata.name}"])
                        if pod_name: break
                    except: pass
                    await asyncio.sleep(2)

                if not pod_name:
                    raise kopf.TemporaryError("Waiting for WordPress pod...", delay=10)

                async def exec_wp(wp_args):
                    return await run_kubectl(["exec", "-n", namespace, pod_name, "-c", "wordpress", "--"] + wp_args)

                await log_step("operator.waiting_wp_core")
                core_ready = False
                for _ in range(30):
                    try:
                        await exec_wp(["wp", "core", "is-installed", "--allow-root"])
                        core_ready = True
                        break
                    except:
                        await asyncio.sleep(3)
                
                if not core_ready:
                    raise kopf.TemporaryError("WordPress core not ready yet", delay=20)

                await log_step("operator.installing_plugins")
                # Install and activate. Using install --activate to be idempotent and safe.
                await exec_wp(["wp", "plugin", "install", "woocommerce", "--activate", "--allow-root"])
                await exec_wp(["wp", "theme", "install", "storefront", "--activate", "--allow-root"])
                
                # CRITICAL: Wait for WooCommerce to be CLI-ready (it takes time after activation)
                await log_step("operator.waiting_woocommerce_api")
                wc_ready = False
                for _ in range(30):
                    try:
                        await exec_wp(["wp", "wc", "product", "list", "--format=count", "--user=admin", "--allow-root"])
                        wc_ready = True
                        break
                    except:
                        await asyncio.sleep(3)
                
                if not wc_ready:
                    logger.warning("woocommerce_api_timeout", store=name)
                    # We'll try to continue, but seeding might fail if WC tables aren't indexed yet

                await asyncio.sleep(5)

                await exec_wp(["wp", "wc", "tool", "run", "install_pages", "--user=admin", "--allow-root"])
                page_ids = await exec_wp(["wp", "post", "list", "--post_type=page", "--format=ids", "--allow-root"])
                if page_ids:
                    for pid in page_ids.split():
                        await exec_wp(["wp", "post", "update", pid, "--post_status=publish", "--allow-root"])
                
                shop_id = await exec_wp(["wp", "post", "list", "--post_type=page", "--name=shop", "--field=ID", "--allow-root"])
                if shop_id:
                    await exec_wp(["wp", "option", "update", "show_on_front", "page", "--allow-root"])
                    await exec_wp(["wp", "option", "update", "page_on_front", shop_id, "--allow-root"])

                try: await exec_wp(["wp", "post", "delete", "1", "--force", "--allow-root"])
                except: pass
                
                try:
                    widgets = await exec_wp(["wp", "widget", "list", "sidebar-1", "--format=ids", "--allow-root"])
                    if widgets:
                        await exec_wp(["wp", "widget", "delete"] + widgets.split() + ["--allow-root"])
                except: pass

                await log_step("operator.seeding_products")

                # First, ensure WooCommerce CLI package is installed
                try:
                    await exec_wp(["wp", "package", "install", "woocommerce/woocommerce-cli:dev-main", "--allow-root"])
                    logger.info("woocommerce_cli_installed")
                except Exception as e:
                    logger.info("woocommerce_cli_already_installed", error=str(e))

                # Verify WooCommerce is ready before creating products
                wc_ready = False
                for attempt in range(30):
                    try:
                        count = await exec_wp(["wp", "wc", "product", "list", "--format=count", "--user=admin", "--allow-root"])
                        wc_ready = True
                        logger.info("woocommerce_ready", attempt=attempt, existing_products=count)
                        break
                    except Exception as e:
                        logger.info("waiting_for_woocommerce", attempt=attempt, error=str(e))
                        await asyncio.sleep(2)

                if not wc_ready:
                    raise Exception("WooCommerce not ready after 60 seconds")

                # Create products with proper visibility settings
                products = [
                    {"name": "Premium Cotton T-Shirt", "type": "simple", "regular_price": "25", "description": "High quality cotton t-shirt", "short_description": "Comfortable everyday wear"},
                    {"name": "Wireless Headphones", "type": "simple", "regular_price": "199", "description": "Immersive sound experience with noise cancellation", "short_description": "Premium audio quality"},
                    {"name": "Ceramic Coffee Mug", "type": "simple", "regular_price": "15", "description": "Perfect for your morning brew", "short_description": "12oz capacity"},
                    {"name": "Eco-Friendly Yoga Mat", "type": "simple", "regular_price": "30", "description": "Non-slip surface for yoga practice", "short_description": "Sustainable materials"},
                    {"name": "Running Shoes", "type": "simple", "regular_price": "85", "description": "Lightweight and durable running shoes", "short_description": "Performance footwear"},
                ]

                created_count = 0
                failed_products = []

                for prod in products:
                    try:
                        # Check if product already exists
                        existing = await exec_wp([
                            "wp", "wc", "product", "list",
                            f"--search={prod['name']}",
                            "--format=ids",
                            "--user=admin",
                            "--allow-root"
                        ])
                        
                        if existing.strip():
                            logger.info("product_exists", name=prod['name'], id=existing.strip())
                            created_count += 1
                            continue
                        
                        # Create product with all required fields
                        cmd = [
                            "wp", "wc", "product", "create",
                            f"--name={prod['name']}",
                            f"--type={prod['type']}",
                            f"--regular_price={prod['regular_price']}",
                            f"--description={prod['description']}",
                            f"--short_description={prod.get('short_description', '')}",
                            "--status=publish",
                            "--catalog_visibility=visible",
                            "--manage_stock=false",
                            "--user=admin",
                            "--porcelain",
                            "--allow-root"
                        ]
                        
                        result = await exec_wp(cmd)
                        product_id = result.strip()
                        
                        if product_id and product_id.isdigit():
                            logger.info("product_created", name=prod['name'], id=product_id)
                            created_count += 1
                        else:
                            logger.warning("product_create_no_id", name=prod['name'], result=result)
                            failed_products.append(prod['name'])
                            
                    except Exception as e:
                        logger.error("product_create_failed", product=prod['name'], error=str(e), error_type=type(e).__name__)
                        failed_products.append(prod['name'])

                logger.info("products_seeded", created=created_count, total=len(products), failed=failed_products)

                # Fail provisioning if NO products were created
                if created_count == 0:
                    raise Exception(f"Failed to create any products (0/{len(products)}). WooCommerce may not be properly configured.")

                await log_step("operator.products_created", {"count": created_count, "failed": failed_products})

                php_fix = """
if (!function_exists('WC')) {
    include_once(ABSPATH . 'wp-content/plugins/woocommerce/woocommerce.php');
}
if (function_exists('WC')) {
    $gateways = WC()->payment_gateways->get_available_payment_gateways();
    foreach ($gateways as $id => $gateway) {
        if ($id === 'cod') {
            update_option('woocommerce_cod_settings', array(
                'enabled' => 'yes', 
                'title' => 'Cash on Delivery', 
                'description' => 'Pay with cash upon delivery.', 
                'instructions' => 'Pay with cash upon delivery.', 
                'enable_for_methods' => array(), 
                'enable_for_virtual' => 'yes'
            ));
            update_option('woocommerce_cod_enabled', 'yes');
        } else {
            update_option('woocommerce_' . $id . '_settings', array('enabled' => 'no'));
            update_option('woocommerce_' . $id . '_enabled', 'no');
        }
    }
    // Set COD as the order gateway
    update_option('woocommerce_gateway_order', array('cod'));
}

try {
    $zones = WC_Shipping_Zones::get_zones();
    $zones[] = array('id' => 0);
    foreach ($zones as $zone_data) {
        $zone = new WC_Shipping_Zone($zone_data['id']);
        $methods = $zone->get_shipping_methods();
        $has_free = false;
        foreach($methods as $instance_id => $method) {
            if ($method->id === 'free_shipping') {
                $has_free = true;
                update_option('woocommerce_free_shipping_' . $instance_id . '_settings', array('enabled' => 'yes', 'title' => 'Free Shipping'));
            } else {
                $zone->delete_shipping_method($instance_id);
            }
        }
        if (!$has_free) { $zone->add_shipping_method('free_shipping'); }
        $zone->save();
    }
} catch (Exception $e) {}
wc_delete_product_transients();
"""
                import base64
                b64_script = base64.b64encode(php_fix.encode('utf-8')).decode('utf-8')
                await exec_wp(["sh", "-c", f"echo {b64_script} | base64 -d > /tmp/fix_store.php"])
                await log_step("operator.configuring_payments")
                try:
                    # Run the shipping/gateway cleanup script
                    await exec_wp(["wp", "eval-file", "/tmp/fix_store.php", "--allow-root"])
                    
                    # Explicitly enable COD via WC-CLI for absolute reliability
                    await exec_wp(["wp", "wc", "payment_gateway", "update", "cod", "--enabled=true", "--user=admin", "--allow-root"])
                    
                    # Final safety check on the option
                    await exec_wp(["wp", "option", "update", "woocommerce_cod_enabled", "yes", "--allow-root"])
                except Exception as e:
                    logger.error("payment_config_failed", error=str(e))

                await log_step("operator.configuration_completed")

            if store:
                if store.status != "ready":
                    store.status = "ready"
                    store.provisioning_completed_at = datetime.datetime.now(datetime.timezone.utc)
                
                store.storefront_url = f"http://{namespace}.{base_domain}"
                store.admin_url = f"http://{namespace}.{base_domain}/wp-admin"
                store.admin_password = wp_password
                await db.commit()
                
                await log_step("operator.completed", {
                    "url": store.storefront_url, 
                    "admin_user": "admin", 
                    "completed_at": store.provisioning_completed_at.isoformat() if store.provisioning_completed_at else None
                })
            
            return {"phase": "Ready", "url": f"http://{namespace}.{base_domain}", "message": "Store provisioned successfully"}

        except Exception as e:
            logger.error("operator_failed", error=str(e))
            if store:
                store.status = "failed"
                store.error_message = str(e)
                await db.commit()
            raise kopf.TemporaryError(f"Provisioning failed: {e}", delay=60)

@kopf.on.delete('stores.urumi.io')
async def delete_store(spec, name, **kwargs):
    namespace = name
    logger.info("operator_delete_event", store=name)
    try:
        await helm_uninstall(namespace, namespace)
        await delete_namespace(namespace)
    except Exception as e:
        logger.error("delete_failed", error=str(e))
    pass
