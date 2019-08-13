Solvers for various kinds of puzzles, using z3. Many of them even work :)

This is not at all very tidy right now; this is more a work-in-progress to
think of what a library built around z3 to make it easy to write solvers
would look like.

This should work with either python2 or python3, but it doesn't work for
  mrwright on python3 (??). Change "pip" to "pip2" or "pip3" and "python" to
  "python2" or "python3" as needed to force a version that works, but be
  consistent.

To get going:

pip install virtualenv
virtualenv venv
. venv/bin/activate  # do just this line each time you come back to the project
pip install -r requirements.txt

Note that this will install the correct package "z3-solver", NOT the totally
  unrelated and unhelpful package named "z3".

Now try it out:

python slitherlink.py

After a moment, you should get a popup with a rendered picture of a solved
  slitherlink.
