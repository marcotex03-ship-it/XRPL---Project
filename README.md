# XRPL---Project

Keep dependencies synced: Whenever someone installs a new library (such as Flask, FastAPI, or Pandas), add it to requirements.txt so teammates can run pip install -r requirements.txt to stay in sync.

Keep branches small and focused: Build one feature per branch and merge often (every day or two). Long-lived branches make merging much harder.

Agree on function inputs and outputs early: Before splitting up, agree on what each module expects (for example, login(username, password) returns True or False) so all parts connect cleanly in main.py.
