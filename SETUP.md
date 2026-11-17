# Setup (5 minutes)

1. Create a **public** repo named exactly your GitHub username (e.g. `wuky/wuky`).
2. Upload everything in this folder, including the hidden `.github/` folder.
3. `README.md` already points to github.com/minte-sys.
4. To change any text, edit the `CONFIG` section at the top of `build.py`.
5. Repo **Settings → Actions → General → Workflow permissions** → "Read and write permissions".
6. **Actions** tab → "Build profile card" → **Run workflow**. Your real stats appear in about a minute,
   then refresh every day.

Optional: to count private repos too, create a classic personal access token with `repo` + `read:user`
scopes and save it as a repo secret named `ACCESS_TOKEN`.

New photo? `python make_ascii.py photo.jpg 76 46 left,top,right,bottom` rewrites the four ascii_/shade_ files
(the crop box is in pixels; aim for head and shoulders).
