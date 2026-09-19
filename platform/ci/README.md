# Self-hosted GitHub Actions Runner

1. GitHub: `Settings → Actions → Runners → New self-hosted runner`.
2. Выбрать Windows x64 и выполнить показанные GitHub команды. Registration token не сохранять в Git.
3. Добавить runner label `unieats`.
4. Установить runner как Windows service командой из инструкции GitHub.
5. Убедиться, что служебная учётная запись runner имеет доступ к Docker Desktop, Git и `kubectl` context `unieats`.

Pipeline выполняет цепочку:

`checkout → Kaniko build → push local Registry → update Helm values → git push → Argo CD auto-sync`.

Kaniko используется как containerized builder и не требует Dockerfile build на runner. Локальный Registry слушает `localhost:5000`; из Minikube он доступен как `host.minikube.internal:5000`.

