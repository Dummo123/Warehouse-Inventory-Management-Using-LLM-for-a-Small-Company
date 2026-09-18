HOW AND WHERE TO RESTORE JWT AUTHORIZATION IN WIM

There are four files to change. Three in the backend/frontend and one optional (logout button). Everything is done in the project root folder (for example D:\smarttherm\ on Windows or ~/smarttherm on Linux).


FILE 1 - BACKEND DEPENDENCIES

Location: app/api/deps.py

What it looks like now (demo mode, auth off):

```
from typing import Optional
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user(token=None, db=Depends(get_db)) -> User:
    user = db.query(User).filter(User.username == "admin").first()
    if user is None:
        user = User(username="admin", full_name="demo", role=UserRole.ADMIN, is_active=True)
    return user

def require_admin(current_user=Depends(get_current_user)) -> User:
    return current_user

def require_operator(current_user=Depends(get_current_user)) -> User:
    return current_user
```

What it should look like after (auth on):

```
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, UserRole
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def require_operator(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role == UserRole.VIEWER:
        raise HTTPException(status_code=403, detail="Operator access required")
    return current_user
```

What changed: the token is now read from the Authorization header, decoded via decode_token from security.py, and the actual user is looked up in the database. Role checks are back.


FILE 2 - FRONTEND AXIOS CLIENT

Location: wim-frontend/src/api/client.ts

What it looks like now:

```
import axios from "axios";
const api = axios.create({ baseURL: "/api" });
export default api;
```

What it should look like after:

```
import axios from "axios";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
    const token = localStorage.getItem("token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (res) => res,
    (err) => {
        if (err.response?.status === 401) {
            localStorage.removeItem("token");
            if (window.location.pathname !== "/login") {
                window.location.href = "/login";
            }
        }
        return Promise.reject(err);
    }
);

export default api;
```

What changed: the request interceptor attaches the token from localStorage to every request. The response interceptor clears the token and redirects to /login whenever the server returns 401 (expired or invalid token).


FILE 3 - FRONTEND ROUTER

Location: wim-frontend/src/App.tsx

You need to do two things: add a RequireAuth wrapper and add the /login route.

Add this helper above the App component:

```
function RequireAuth({ children }: { children: React.ReactNode }) {
    if (!localStorage.getItem("token")) {
        return <Navigate to="/login" replace />;
    }
    return <>{children}</>;
}
```

Import the LoginPage at the top:

```
import LoginPage from "./pages/LoginPage";
```

Change the Routes section so that /login is outside the layout, and the layout is wrapped in RequireAuth:

```
<Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/" element={
        <RequireAuth>
            <AppLayout />
        </RequireAuth>
    }>
        <Route index element={<Navigate to="/stock" replace />} />
        <Route path="stock" element={<StockPage />} />
        <Route path="movements" element={<MovementsPage />} />
        <Route path="articles" element={<ArticlesPage />} />
        <Route path="purchases" element={<PurchasesPage />} />
        <Route path="purchases/new" element={<PurchaseFormPage />} />
        <Route path="production" element={<ProductionPage />} />
        <Route path="production/new" element={<ProductionFormPage />} />
        <Route path="shipments" element={<ShipmentsPage />} />
        <Route path="shipments/new" element={<ShipmentFormPage />} />
        <Route path="returns" element={<ReturnsPage />} />
        <Route path="returns/new" element={<ReturnFormPage />} />
        <Route path="finance" element={<FinancePage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="assistant" element={<AssistantPage />} />
    </Route>
    <Route path="*" element={<Navigate to="/login" replace />} />
</Routes>
```

What changed: unauthenticated users land on /login and never see the layout. After login they go to /stock. The catch-all route sends unknown paths to /login instead of /stock.

The LoginPage.tsx and useAuth.ts files already exist and work. Do not delete them, just reconnect them by adding the route as shown above.


FILE 4 - OPTIONAL, LOGOUT BUTTON

Location: wim-frontend/src/components/layout/AppLayout.tsx

In the current version the logout button was removed. If you want it back, add inside the Sider, below the Menu:

```
<div style={{ padding: 16, borderTop: "1px solid #f0f0f0" }}>
    <Button
        block
        onClick={() => {
            localStorage.removeItem("token");
            window.location.href = "/login";
        }}
    >
        Sign out
    </Button>
</div>
```

Import Button from antd at the top of the file. This is optional, but useful for the demo, because it lets you show the login flow repeatedly without clearing localStorage manually in DevTools.


AFTER ALL CHANGES - RESTART AND AUTHORIZE

Step 1. Restart the backend. If it runs with --reload, it will pick up the deps.py changes on its own. Otherwise press Ctrl+C in the backend terminal and run again:

```
uvicorn app.main:app --reload
```

Step 2. If the frontend dev server is running, it will also hot reload. If not, from wim-frontend:

```
npm start
```

Step 3. Make sure an admin user exists in the database. The seed script creates one on first import. If you never ran it, run:

```
python scripts/seed_data.py --excel warehouse_report.xlsx
```

The default credentials are admin / admin123, as set in .env.

Step 4. Open the frontend in a browser (usually http://localhost:3000). You will be redirected to /login.

Step 5. Enter admin as the username and admin123 as the password. Click Sign in.

Step 6. The frontend sends POST /api/auth/login as form-data. The backend verifies the password with bcrypt, creates a JWT via create_access_token, and returns access_token. The useAuth hook stores it in localStorage under the key token and redirects to /stock.

Step 7. From now on every request from the frontend includes the header Authorization: Bearer <token>. The backend deps.py decodes it and returns the real user. Role checks apply as before (operator cannot be viewer, admin has extra privileges on user management endpoints).

Step 8. If the token expires (8 hours by default, set by ACCESS_TOKEN_EXPIRE_MINUTES), any request will return 401, the response interceptor clears localStorage and redirects back to /login. Log in again to continue.


VERIFYING IT WORKS

Backend check without the frontend, run from a terminal:

```
curl -X POST http://localhost:8000/api/auth/login -d "username=admin&password=admin123"
```

You should get back JSON with an access_token field. Copy that token and use it like this:

```
curl http://localhost:8000/api/stock -H "Authorization: Bearer <paste token here>"
```

If you get a JSON list of stock records, the backend is fully restored. If you get 401, the token was wrong or expired. If you get 403 on some endpoints, the current user role does not have rights for that endpoint (this is correct behavior for a viewer).

Frontend check: open DevTools, Network tab, refresh the page. The first request to /api/stock should show a Request Header called Authorization with value Bearer eyJ... If it is missing, the client.ts interceptor was not saved correctly, or the token is not in localStorage under the key token.


COMMON PITFALLS

If you get redirected to /login in a loop after logging in, it means the token was saved but the backend still returns 401. Check that SECRET_KEY in .env is identical between the process that signs the token and the process that verifies it. If you changed it, restart the backend.

If POST /api/auth/login returns 422, you sent JSON. The endpoint expects form-data (OAuth2PasswordRequestForm). The frontend already sends it correctly.

If you see the error "module bcrypt has no attribute about", run:

```
pip install "bcrypt==4.0.1" --force-reinstall
```

If the login page loads but the Sign in button does nothing, check the browser console. Common cause: proxy in package.json was removed. Verify that wim-frontend/package.json still has "proxy": "http://localhost:8000".


SUMMARY OF FILES TOUCHED

app/api/deps.py - rewrite three functions to read and validate the JWT.
wim-frontend/src/api/client.ts - add request and response interceptors.
wim-frontend/src/App.tsx - add RequireAuth wrapper, add /login route.
wim-frontend/src/components/layout/AppLayout.tsx - optional, add Sign out button.

No database changes are needed. The users table already exists and has the admin row created by seed. No changes to security.py, models.py, auth.py, or any other file.