# illuminatingfish.github.io

The resume source is `resume/main.tex`. The website displays
`folder/Intern_Resume.pdf`.

Edit the source, then build a local PDF with XeLaTeX:

```sh
python scripts/sync_resume.py
```

Check for conflicting Overleaf edits and build without publishing:

```sh
python scripts/sync_resume.py --check
```

Publish the source to Overleaf and the compiled PDF and website updates to GitHub:

```sh
python scripts/sync_resume.py --publish
```

The Overleaf project is
<https://www.overleaf.com/project/6924d7d389c04e818231d7da>.
Its Git URL, branch, and last synchronized commit are recorded in
`resume/overleaf.json`. Authentication uses the existing Git credential helper;
credentials are not stored in this repository.

This is an explicitly run local synchronization script, not Overleaf's native
GitHub integration or an automatic background sync. It preserves other files
in the Overleaf project and stops if that project's source has changed since
the last synchronization. Merge and review any Overleaf edits locally before
updating the recorded commit and publishing again. Git pushes use normal
fast-forward checks and never force-push.

Publishing updates Overleaf first, then GitHub. If the GitHub step fails, fix
the reported issue and rerun the command. A matching Overleaf source is safe
to retry. The existing local `push.sh` still only publishes the website;
use `sync_resume.py --publish` for resume changes.
