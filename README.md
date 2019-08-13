Solvers for various kinds of puzzles, using z3. Many of them even work :)

This is not at all very tidy right now; this is more a work-in-progress to
think of what a library built around z3 to make it easy to write solvers
would look like.

Note that only python2 is supported at this time.

To get going:

pip2 install virtualenv
virtualenv venv
. venv/bin/activate  # do just this line each time you come back to the project
pip2 install -r requirements.txt

Note that this will install the correct package "z3-solver", NOT the totally
  unrelated and unhelpful package named "z3".

Now try it out:

python2 slitherlink.py

After a moment, you should get a popup with a rendered picture of a solved
  slitherlink.
