### Contributing

Vibora is developed on GitHub and pull requests are welcome but there
are few guidelines:

1) Introduction of new external dependencies is highly discouraged
and will probably not be merged.

2) Patches that downgrade the overall framework performance, unless
security/fix ones, will need to prove great value in functionality
to be merged.

3) Bug fixes must include tests that fail/pass in respective versions.

4) PEP 8 must be followed with the exception of the
max line size which is currently 120 instead of 80 chars wide.

### Reporting an issue

1) Describe what you expected to happen and what actually happens.

2) If possible, include a minimal but complete example
to help us reproduce the issue.

3) We'll try to fix it as soon as possible but be in mind that
Vibora is open source and you can probably submit a pull request
to fix it even faster.

### First time setup

1) Clone Vibora repository.

2) Create a virtualenv and install the dependencies listed on
requirements.txt

3) Run build.py (Vibora has a lot of cython extensions and this file
helps to build them so you can test your code without the need to
install or compile libraries manually.