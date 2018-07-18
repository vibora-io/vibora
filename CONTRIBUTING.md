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

## Commit Message Guidelines

## Question or Problem?
Please don't create issues if you have a question about a problem or the library.
We have many open issues and to keep track of them it would be good to outsource questions.

If you haven't found any help in the [documentation](https://docs.vibora.io/), ask for help in our [Slack channel](https://join.slack.com/t/vibora-io/shared_invite/enQtNDAxMTQ4NDc5NDYzLTA2YTdmNmM0YmY4ZTY0Y2JjZjc0ODgwMmJjY2I0MmVkODFiYzc4YjM0NGMyOTkxMjZlNTliZDU1ZmFhYWZmNjU), someone will surely take time for your problem.

## Found a bug or want a feature?
Das erste was du bitte prüfst, ist ob es schon ein Issue zu diesem Fehler oder dieser Funktionalität gibt, damit es keine Dopplungen der gleichen Themen gibt.

Wenn es kein Issue zu deinem Thema gibt würden wir uns sehr freuen wenn du uns eins dazu erstellst. Fülle dazu einfach die vorgegebene Vorlage und wähle einen sinnvollen Namen für das Issue.

Besser wäre es natürlich wenn du direkt einen Pull Request mit dem zu behebenden fehler oder neuen funktionalität erstellen kannst.

### Submitting a Pull Request
1. Fork this project.
2. Clone your forked repository .
2. Create a new branch from our `develop` branch with `git checkout develop` and `git checkout -b my-branch-name`. 
3. Create your patch **including software tests**.
4. Follow our [Coding Style](#coding-style).
4. Add your changed files (`git add my-file`) and commit your changes with `git commit -m "my-changes"`. If you want to add all files directly to the commit you can easly do `git commit -am "my-commit"`. Please following our [Commit Message Guidelines](#commit-message-guidelines).
5. Push your branch to Github: `git push origin my-branch-name`.
6. In Github send a Pull Request to `vibora:develop`.
* If we suggest changes:
  * Make the required changes
  * Run tests if everythin is working as excepected
  * Commit you changes
  * Push your changes

### After your Pull Request is merged
1. Delete your branch with `git push origin --delete my-branc-name`
2. Checkout `master` or `develop` and delete your local branch with `git branch -D my-branch-name`
3. Update your `develop` branch with `git pull --ff upstream master` to be ready for the next changes.
