# Config Precedence FastAPI

## Deploy to Vercel

1. Extract this ZIP.
2. Upload the folder to a new GitHub repository.
3. In Vercel, choose **Add New → Project**, import that repository, and deploy.
4. Once deployment succeeds, test:
   `https://YOUR-PROJECT.vercel.app/effective-config`
5. Paste that endpoint URL into the assignment.

Test query overrides:
`https://YOUR-PROJECT.vercel.app/effective-config?set=port=9000&set=debug=true`

Expected base values when no query overrides are supplied:
`port=8775`, `workers=10`, `debug=true`, `log_level=debug`, `api_key=****`.

The API accepts repeated `set` query parameters, coerces `port`/`workers` to integers and `debug` to a boolean, and always masks `api_key`.
