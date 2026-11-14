


## 1. What is `git stash`?

**`git stash` temporarily saves your uncommitted changes without creating a commit.**

It allows you to clean your working directory so you can perform operations such as `git pull`.

쉽게 말하면, **현재 수정 중인 파일을 임시 보관한 후 나중에 다시 복원하는 기능**입니다.



현재 오류는 로컬에서 수정한 `.obsidian/workspace.json` 파일이 원격 파일과 충돌할 가능성이 있어 Git이 병합을 중단한 것입니다.

**로컬 변경 사항을 보존하면서 `git pull --no-rebase`를 실행하려면 `git stash`를 사용하면 됩니다.**

### 1. 로컬 변경 사항 임시 저장

```
git stash push -m "backup workspace"
```

수정된 `.obsidian/workspace.json` 파일을 임시 저장합니다.

### 2. 원격 저장소 가져오기

```
git pull --no-rebase origin main
```

로컬 커밋 1개와 원격 커밋 26개를 병합합니다.

**주의:** 이 단계에서도 커밋 간 충돌이 발생할 수 있습니다. 충돌이 발생하면 해결하기 전까지 다음 단계로 진행하지 마세요.

### 3. 로컬 변경 사항 복원

병합이 성공했다면 다음 명령을 실행합니다.

```
git stash pop
```

임시 저장한 파일을 복원합니다. 이 과정에서도 충돌이 발생할 수 있습니다.

### 4. Git 상태 확인

```
git status
```

### 5. 원격 저장소에 반영

병합이 완료되었다면:

```
git push origin main
```

미커밋 상태로 남은 `workspace.json` 수정 사항은 push되지 않습니다.

---

### 추가 권장 사항

`.obsidian/workspace.json`은 Obsidian의 창 배치, 열린 문서 등 작업 환경을 저장하는 파일입니다.

이 파일은 자주 변경되므로 Git에서 추적하지 않는 것이 편리할 수 있습니다.

다만 현재는 기존 커밋의 병합이 우선입니다.

**지금은 다음 두 명령어를 순서대로 실행하세요.**

```
git stash
git pull --no-rebase origin main
```

실행 결과를 보여주시면 충돌 여부에 따라 다음 명령어를 안내하겠습니다.