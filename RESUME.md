# 🌅 Good Morning! How to Resume

To restart the Urumi Platform exactly where you left off (with all fixes applied):

### 1. Start the Cluster
Open a terminal in this folder and run:
```powershell
k3d cluster start urumi-cluster
```
*(If the cluster was deleted or you want a fresh start, run `.\scripts\setup-local.ps1` instead)*.

### 2. Connect Dashboard & API
Run the robust connection script (this opens two windows to keep connections alive):
```powershell
.\connect-all.ps1
```

### 3. Open Dashboard
Go to: **http://localhost:8081**

---

### Troubleshooting
*   **"Quota Exceeded"**: The database persists. If you used up 50 slots, run:
    ```powershell
    kubectl exec -n urumi-platform platform-db-0 -- sh -c "PGPASSWORD=urumi123 psql -U urumi -d urumi -c 'DELETE FROM stores;'"
    ```
*   **"Site can't be reached"**: Close the port-forward windows and run `.\connect-all.ps1` again.
