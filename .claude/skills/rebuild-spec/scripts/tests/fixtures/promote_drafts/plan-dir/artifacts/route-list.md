# Route List

| Code | Method | Path | Handler | Auth |
|------|--------|------|---------|------|
| ROUTE001 | POST | /login | AuthController@login | public |
| ROUTE002 | POST | /logout | AuthController@logout | auth |
| ROUTE003 | GET | /profile | ProfileController@show | auth |
