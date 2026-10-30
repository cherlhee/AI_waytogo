




  

how to know git orign address

To check your Git origin address (remote URL), run:

```
git remote -v
```

Example output:

`origin https://github.com/cherlhee/AI_waytogo.git (fetch) origin https://github.com/cherlhee/AI_waytogo.git (push)`

To display only the origin URL, use:

```
git remote get-url origin
```

To see more information about the remote repository:

```
git remote show origin
```

Note: Run these commands inside your Git project folder (the folder containing `.git`).

how to know whether origin is master or main

To check whether your GitHub `origin` uses main or master, use:

### 1. Check the default branch of origin

```
git remote show origin
```

Example output:

`* remote origin Fetch URL: https://github.com/cherlhee/AI_waytogo.git Push URL: https://github.com/cherlhee/AI_waytogo.git HEAD branch: main`

`HEAD branch: main` means the default branch on GitHub is `main`.

### 2. Check your local branch

```
git branch
```

Example:

`* master main`

The `*` indicates your current local branch.

### 3. Check all local and remote branches

```
git branch -a
```

Example:

`* master remotes/origin/main`

This means:

- Local branch: `master`
    
- Remote branch: `origin/main`
    

### 4. Check which remote branch your local branch tracks

```
git branch -vv
```

Example:

`* main abc1234 [origin/main] Latest commit`

This means your local `main` tracks `origin/main`.

### 5. Change local master to main (if necessary)

```
git branch -M main
git branch --set-upstream-to=origin/main main
```

The second command requires `origin/main` to exist locally as a remote-tracking branch. Run `git fetch origin` first if necessary.

Recommended command:

```
git remote show origin
```

Look for `HEAD branch: main` or `HEAD branch: master`.

waytogo> git remote show origin * remote origin Fetch URL: https://github.com/cherlhee/AI_waytogo.git Push URL: https://github.com/cherlhee/AI_waytogo.git HEAD branch: main Remote branches: main tracked master tracked Local branch configured for 'git pull': main merges with remote master Local ref configured for 'git push': main pushes to main (local out of date) (base) PS C:\CHERLHEE\AI_waytogo>

Your Git configuration has a branch mismatch.

`HEAD branch: main Remote branches: main tracked master tracked Local branch configured for 'git pull': main merges with remote master Local ref configured for 'git push': main pushes to main (local out of date)`

### Current configuration

|Item|Current setting|
|---|---|
|GitHub default branch|`main`|
|GitHub remote branches|`main`, `master`|
|Local branch|`main`|
|`git pull` target|`origin/master`|
|`git push` target|`origin/main`|

Problem: `git pull` uses `master`, but `git push` uses `main`.

### 1. Fix Git pull to use origin/main

Run:

```
git branch --set-upstream-to=origin/main main
```

### 2. Verify the configuration

```
git remote show origin
```

Expected result:

`Local branch configured for 'git pull': main merges with remote main Local ref configured for 'git push': main pushes to main`

### 3. Synchronize with GitHub

First check for uncommitted changes:

```
git status
```

Then, if your working tree is clean:

```
git pull --ff-only origin main
```

If Git reports that the branches have diverged, inspect the history before choosing merge or rebase.

### 4. Future Git commands

After fixing the upstream branch, you can use:

```
git pull
git add .
git commit -m "Update files"
git push
```

Recommendation: Use `main` consistently for both pull and push. You do not need to delete the remote `master` branch to do this.

Your most important command right now is:

```
git branch --set-upstream-to=origin/main main
```

waytogo> git pull hint: You have divergent branches and need to specify how to reconcile them. hint: You can do so by running one of the following commands sometime before hint: your next pull: hint: hint: git config pull.rebase false # merge hint: git config pull.rebase true # rebase hint: git config pull.ff only # fast-forward only hint: hint: You can replace "git config" with "git config --global" to set a default hint: preference for all repositories. You can also pass --rebase, --no-rebase, hint: or --ff-only on the command line to override the configured default per hint: invocation. fatal: Need to specify how to reconcile divergent branches. (base) PS C:\CHERLHEE\AI_waytogo>

This error means your local `main` and GitHub `origin/main` have different commits. Git needs you to choose how to combine them.

### 1. Recommended solution: Merge

For your `AI_waytogo` project, use:

```
git pull --no-rebase origin main
```

This merges the GitHub changes into your local branch while preserving both histories.

Before running it, check:

```
git status
```

If you have uncommitted changes, commit or stash them first.

### 2. Set merge as the default

To prevent the same error in the future:

```
git config pull.rebase false
```

Then you can use:

```
git pull
```

### 3. Other options

|Command|Meaning|
|---|---|
|`git pull --no-rebase origin main`|Merge local and remote histories|
|`git pull --rebase origin main`|Replay local commits on top of remote commits|
|`git pull --ff-only origin main`|Pull only when no divergent history exists|

### 4. Check and push

After resolving any merge conflicts:

```
git status
git push origin main
```

Important: Do not use `git push --force` to solve this problem, because it could overwrite commits on GitHub.

Since your repository previously had both `master` and `main`, I recommend verifying the tracking branch as well:

```
git branch -vv
```

You should see `[origin/main]` beside your local `main` branch.

If `git pull --no-rebase origin main` produces a conflict, paste the error here and I can show you exactly how to resolve it without losing your files.

//////////////

obsidian. theme; wasp.


```python

git stash push -u -m "backup before pull"
git pull origin main
git status


git config --global user.email "cherlhee@jcradar.com"`
git config --global user.name "cherlhee"


git commit -m "append slamkit"
git push
git pull
git status


git clone https://github.com/cherlhee/AI_waytogo.git
git clone -b master https://github.com/cherlhee/AI_waytogo.git


```

### 추천 설정

현재 Obsidian에서 GitHub와 Markdown을 함께 사용한다면 다음 구성을 추천합니다.

|항목|추천|
|---|---|
|Interface font|맑은 고딕|
|Text font|Noto Sans KR|
|Monospace font|D2Coding|
|본문 크기|16~17px|





  

`(base) C:\__PROJECTed\SLAM_SStech\SLAM_KIT\AI_waytogo>git pull remote: Enumerating objects: 126, done. remote: Counting objects: 100% (126/126), done. remote: Compressing objects: 100% (102/102), done. remote: Total 117 (delta 17), reused 112 (delta 12), pack-reused 0 (from 0) Receiving objects: 100% (117/117), 7.31 MiB | 6.80 MiB/s, done. Resolving deltas: 100% (17/17), completed with 4 local objects. From https://github.com/cherlhee/AI_waytogo 9e8fcff..ea646b1 main -> origin/main Updating 9e8fcff..ea646b1 error: Your local changes to the following files would be overwritten by merge: .obsidian/workspace.json Please commit your changes or stash them before you merge. error: The following untracked working tree files would be overwritten by merge: .obsidian/themes/Ukiyo/manifest.json .obsidian/themes/Ukiyo/theme.css RESEARCH/SLAM/slamKIT/BATTERY-02.md Please move or remove them before you merge. Aborting`



현재 git pull이 실패한 이유는 **로컬 파일과 GitHub 파일이 충돌하기 때문**입니다.

GitHub에서 파일 다운로드는 완료되었지만, 로컬 파일을 보호하기 위해 병합(Merge)이 중단되었습니다.

## 1. 오류 원인

충돌 파일은 다음과 같습니다.

|파일|문제|
|---|---|
|.obsidian/workspace.json|로컬에서 수정한 파일|
|.obsidian/themes/Ukiyo/manifest.json|로컬에만 존재하는 파일|
|.obsidian/themes/Ukiyo/theme.css|로컬에만 존재하는 파일|
|RESEARCH/SLAM/slamKIT/BATTERY-02.md|로컬에만 존재하는 파일|

특히 BATTERY-02.md는 연구 자료이므로 삭제하지 않는 것이 좋습니다.

---

## 2. 해결 방법 (추천)

**로컬 파일을 임시 보관한 다음 GitHub 파일을 가져오는 방법**입니다.

현재 디렉터리에서 다음 명령어를 순서대로 실행하세요.

### ① 로컬 변경 파일 임시 보관

```
git stash push -u -m "backup before pull"
```

여기서 -u는 Git에서 추적하지 않는 새 파일까지 임시 보관한다는 의미입니다.

### ② GitHub에서 최신 파일 가져오기

```
git pull origin main
```

이제 GitHub의 최신 파일이 로컬에 반영됩니다.

### ③ 임시 보관한 로컬 파일 복원

```
git stash pop
```

**주의:** GitHub와 로컬에 동일한 파일이 존재하면 이 단계에서 충돌이 발생할 수 있습니다. 특히 BATTERY-02.md와 Obsidian 테마 파일에서 충돌할 가능성이 있습니다.

충돌이 발생하면 파일을 바로 삭제하지 말고 상태를 확인하세요.

```
git status
```

---

## 3. 가장 안전한 방법

로컬에서 작성한 연구 자료를 유지해야 한다면 다음 방법을 권장합니다.

먼저 백업합니다.

```
Copy-Item .\RESEARCH\SLAM\slamKIT\BATTERY-02.md ..\BATTERY-02_backup.md
```

그다음 다음 명령어를 실행합니다.

```
git stash push -u -m "backup before pull"

git pull origin main
```

여기까지만 실행하면 GitHub 최신 파일이 반영되고, 로컬 변경 사항은 stash에 안전하게 보관됩니다.

이후 필요할 때 다음 명령어로 확인할 수 있습니다.

```
git stash list
```

로컬 변경 사항을 다시 적용하려면:

```
git stash apply
```

충돌이 해결되기 전에는 git stash drop을 실행하지 마세요.

---

## 4. Obsidian 사용 시 추가 권장 사항

.obsidian/workspace.json은 Obsidian을 사용할 때 자주 변경되는 파일입니다.

따라서 GitHub 동기화에서 제외하는 것이 좋습니다.

프로젝트의 .gitignore 파일에 다음 내용을 추가하세요.

`# Obsidian workspace .obsidian/workspace.json .obsidian/workspace-mobile.json`

단, 이미 Git에서 관리 중인 파일은 .gitignore에 추가하는 것만으로 제외되지 않습니다.

다음 명령어가 추가로 필요합니다.

```
git rm --cached .obsidian/workspace.json
```

이 명령어는 로컬 파일을 삭제하지 않고 Git 추적만 해제합니다. 이후 커밋하여 GitHub에도 반영해야 합니다.

---

### 결론

현재 상황에서는 다음 두 명령어부터 실행하는 것이 좋습니다.

```
git stash push -u -m "backup before pull"
git pull origin main
```

**질문:** 현재 BATTERY-02.md 파일은 GitHub 파일과 로컬 파일 중 어느 것을 유지하고 싶으신가요?

1. **GitHub 파일 유지** — GitHub의 최신 버전을 사용
2. **로컬 파일 유지** — 현재 PC에서 작성한 내용을 사용
3. **두 파일 모두 유지** — 서로 다른 이름으로 저장

선택에 따라 충돌 없이 처리하는 명령어가 달라집니다.

1번

**1번: GitHub 파일을 유지**하려면 로컬의 충돌 파일을 정리한 후 git pull을 실행하면 됩니다.

가장 간단한 방법은 다음과 같습니다.

### 1. 로컬 변경 사항 임시 보관

```
git stash push -u -m "backup before pull"
```

### 2. GitHub 최신 파일 가져오기

```
git pull origin main
```

### 3. 결과 확인

```
git status
```

정상적으로 완료되면 다음과 비슷하게 출력됩니다.

`On branch main Your branch is up to date with 'origin/main'. nothing to commit, working tree clean`

### 4. 주의사항

**GitHub 파일을 유지하려면 git stash pop을 실행하지 마세요.**

git stash pop을 실행하면 이전 로컬 파일이 다시 적용되어 충돌할 수 있습니다.

임시 보관한 파일은 다음 명령어로 확인할 수 있습니다.

```
git stash list
```

### 최종 명령어

```
git stash push -u -m "backup before pull"
git pull origin main
git status
```

이렇게 하면 **GitHub의 최신 파일을 가져오면서 기존 로컬 변경 사항은 stash에 백업**됩니다.

참고로 이 방법은 GitHub에 없는 다른 로컬 변경 사항도 임시 보관합니다.

ytogo>git pull origin main From https://github.com/cherlhee/AI_waytogo * branch main -> FETCH_HEAD Updating 9e8fcff..ea646b1 error: Your local changes to the following files would be overwritten by merge: .obsidian/workspace.json Please commit your changes or stash them before you merge. Aborting

현재 .obsidian/workspace.json 파일이 로컬에서 수정되어 git pull이 중단되었습니다.

**GitHub 파일을 유지하기로 하셨으므로**, 로컬의 해당 파일을 원래 상태로 되돌린 후 다시 다운로드하면 됩니다.

### 1. Obsidian 설정 파일 복원

```
git restore .obsidian/workspace.json
```

이 명령어는 로컬의 workspace.json 변경 사항을 취소합니다.

### 2. GitHub 최신 파일 가져오기

```
git pull origin main
```

### 3. 결과 확인

```
git status
```

### 주의사항

이전에 다음과 같은 파일도 충돌했습니다.

- .obsidian/themes/Ukiyo/manifest.json
- .obsidian/themes/Ukiyo/theme.css
- RESEARCH/SLAM/slamKIT/BATTERY-02.md

이 파일들이 여전히 존재하면 다시 충돌할 수 있습니다.

**따라서 가장 안전한 방법은 다음 명령어를 실행하는 것입니다.**

```
git stash push -u -m "backup before pull"
git pull origin main
git status
```

git stash는 로컬 변경 파일과 새 파일을 임시 보관합니다. GitHub 파일을 유지하려면 git stash pop은 실행하지 마세요.

**추천:** 위의 세 명령어를 순서대로 실행하세요.