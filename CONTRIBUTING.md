# Contributing to Vibora

We are very happy if you plan help us make Vibora better. This project is very complex and must remain structured. Please read our guidelines for contribute to this project.

* [Code of Conduct](#code-of-conduct)
* [Coding Style](#coding-style)
* [Commit Message Guidelines](#commit-message-guidelines)
* [Question or Problem?](#question-or-problem)
* [Found a bug or want a feature?](#found-a-bug-or-want-a-feature)

## Code of Conduct
To keep this project open and transparent, please read our [Code of Conduct](.github/CODE_OF_CONDUCT.md).

## Coding Style
This section is especially important because consistent and clean code is an important step for a good and big project.

Vibora tries to use bleeding edge technologies from python. Among other things, guys.
Therefore, please make sure to use [type annotations](https://docs.python.org/3/library/typing.html) as good as possible.

Another example of good code would be the use of:
```python
world ="World"
"f "Hello {world}"
```
instead of:
```
"Hello {0}".format(world)
```
or:
```python
"Hello %s" % (world)
```
this is old python, please don't use it.

## Commit Message Guidelines
Correctly formatted commit messages are very important. Changelogs are automatically generated from commit messages. Therefore, please take the time to write the message cleanly and in detail.

A commit message consists of four main components. A **type**, short **description**, the **main part** and the **footer**. In the following sections these four components are explained in more detail.

The structure of a commit message should look like this.
```
<type>: <descriptio>
<BLANK LINE>
<main part>
<BLANK LINE>
<footer>
```

### Type
The type describes what kind of commit it is. Possible types are listed here:

* **feat** A new feature
* **docs** New documentation or a fix for documentation
* **fix** A bug fix
* **refactor** A change to the code that is neither a new functionality nor a bug fix
* **ci** Changes on the CI configuration
* **test** Adding missing tests or fixing one
* **style** Changes on code style
* **perf** Changes that improve performance

### Subject
The subject should be short and summarize what the commit does. Please use the **imperative form**. So not "changed" but "change". Do **not** write any **dots** at the end of the sentence and do **not** start with a **capital letter**.

### Body


### Footer


## Question or Problem?
Please don't create issues if you have a question about a problem or the library.
We have many open issues and to keep track of them it would be good to outsource questions.

If you haven't found any help in the [documentation](https://docs.vibora.io/), ask for help in our [Slack channel](https://join.slack.com/t/vibora-io/shared_invite/enQtNDAxMTQ4NDc5NDYzLTA2YTdmNmM0YmY4ZTY0Y2JjZjc0ODgwMmJjY2I0MmVkODFiYzc4YjM0NGMyOTkxMjZlNTliZDU1ZmFhYWZmNjU), someone will surely take time for your problem.

## Found a bug or want a feature?
The first thing you should check is whether there is already an issue for this error or this functionality, so that there are no duplications of the same topics.

If there is no issue to your topic we would be very happy if you create one for us. Simply fill in the given template and choose a meaningful name for the issue.

Of course it would be better if you could directly create a pull request with the error or new functionality you want to fix.

### Submitting a Pull Request
1. Fork this project.
2. Clone your forked repository .
3. Create a new branch from our `develop` branch with `git checkout develop` and `git checkout -b my-branch-name`.
4. Install requirements from `requirements-dev.txt`
5. Create your patch **including software tests**.
6. Follow our [Coding Style](#coding-style).
. Add your changed files (`git add my-file`) and commit your changes with `git commit -m "my-changes"`. If you want to add all files directly to the commit you can easly do `git commit -am "my-commit"`. Please following our [Commit Message Guidelines](#commit-message-guidelines).
7. Push your branch to Github: `git push origin my-branch-name`.
8. In Github send a Pull Request to `vibora:develop`.
* If we suggest changes:
  * Make the required changes
  * Run tests if everythin is working as excepected
  * Commit you changes
  * Push your changes

### After your Pull Request is merged
1. Delete your branch with `git push origin --delete my-branc-name`
2. Checkout `master` or `develop` and delete your local branch with `git branch -D my-branch-name`
3. Update your `develop` branch with `git pull --ff upstream master` to be ready for the next changes.
