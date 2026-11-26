


wls + docker

# WSL + Docker 설치 및 사용 방법

**WSL(Windows Subsystem for Linux) + Docker**를 사용하면 Windows 환경에서 Linux를 실행하고, Docker 컨테이너를 통해 Python, MySQL, AI 모델 등을 운영할 수 있습니다.

## 1. WSL과 Docker의 관계

`Windows 11 │ ├── WSL2 │ └── Ubuntu 22.04 │ ├── Python │ ├── AI / LSTM │ └── Linux 개발환경 │ └── Docker Desktop │ └── WSL2 Backend ├── Container 1 : MySQL ├── Container 2 : Python ├── Container 3 : AI Prediction └── Container 4 : ROS2`

- **WSL2:** Windows에서 Linux를 실행하는 환경
- **Docker:** 애플리케이션을 독립적인 컨테이너에서 실행하는 플랫폼
- **Docker Desktop:** Windows에서 Docker를 관리하는 프로그램

Docker Desktop은 WSL2를 백엔드로 사용하여 Linux 컨테이너를 실행할 수 있습니다.

## 2. WSL2 설치

Windows PowerShell을 관리자 권한으로 실행합니다.

```
wsl --install
```

설치 후 컴퓨터를 재부팅합니다.

WSL 상태 확인:

```
wsl --status
```

설치된 Linux 확인:

```
wsl -l -v
```

예상 결과:

`NAME STATE VERSION Ubuntu Running 2`

Ubuntu 22.04를 설치하려면:

```
wsl --install -d Ubuntu-22.04
```

Ubuntu 실행:

```
wsl -d Ubuntu-22.04
```

## 3. Docker Desktop 설치

공식 설치 사이트:

[Docker Desktop 다운로드](https://www.docker.com/products/docker-desktop/?utm_source=chatgpt.com)

설치할 때 **Use WSL 2 instead of Hyper-V** 옵션을 선택합니다.

설치 후 Docker Desktop에서 다음을 설정합니다.

**Settings → General**

- Use the WSL 2 based engine 활성화

**Settings → Resources → WSL Integration**

- Ubuntu-22.04 활성화

이렇게 하면 Ubuntu 터미널에서도 Docker 명령어를 사용할 수 있습니다.

## 4. Docker 실행 확인

Ubuntu 터미널에서:

```
docker --version
```

Docker 테스트:

```
docker run hello-world
```

정상 실행되면 다음 메시지가 출력됩니다.

`Hello from Docker!`

## 5. Python 컨테이너 실행

Python 3.11 환경을 실행하려면:

```
docker run -it --name python-test python:3.11 bash
```

컨테이너 내부에서:

```
python --version
```

Python 프로그램 실행:

```
python
```

print("Hello Docker")

컨테이너에서 나가기:

```
exit
```

다시 실행:

```
docker start -ai python-test
```

## 6. Docker에서 MySQL 실행

```
docker run -d \
  --name mysql-server \
  -e MYSQL_ROOT_PASSWORD=change_me \
  -e MYSQL_DATABASE=airpredict \
  -p 3307:3306 \
  -v mysql_data:/var/lib/mysql \
  mysql:8.0
```

MySQL 접속 정보:

|항목|값|
|---|---|
|Host|localhost|
|Port|3307|
|Database|airpredict|
|User|root|
|Password|change_me|

실제 운영에서는 예시 비밀번호를 강력한 비밀번호로 변경하고, 별도의 애플리케이션 계정을 만드는 것이 좋습니다.

## 7. WSL과 Docker의 차이

|구분|WSL2|Docker|
|---|---|---|
|목적|Linux 실행 환경|애플리케이션 격리|
|운영체제|Linux 배포판 실행|호스트 커널 공유|
|Python 실행|가능|가능|
|MySQL 실행|가능|가능|
|AI 모델 실행|가능|가능|
|환경 재현|수동 설정 필요|Dockerfile로 재현|
|배포|상대적으로 복잡|비교적 간단|

## 8. AI 프로젝트에 적용

현재 개발 중인 **MEGACOM 압축기 오일온도 예측 시스템**에도 사용할 수 있습니다.

예를 들어 다음과 같이 구성할 수 있습니다.

`Windows │ └── WSL2 Ubuntu │ └── Docker │ ├── CF Prediction │ └── cf.py │ ├── LSTM Prediction │ └── lstm_predict.py │ └── MySQL ├── ai_data ├── ai_oiltemp └── ai_lstm_r`

실제 MySQL이 외부 서버에서 운영되고 있다면 Docker에 MySQL을 새로 설치할 필요 없이 기존 서버에 연결하면 됩니다.

**질문:** WSL + Docker를 사용하려는 목적이 다음 중 어느 것인가요?

1. **Windows에서 Linux 개발환경 구축**
2. **Python + MySQL + AI 예측 프로그램을 Docker로 실행**
3. **Jetson Orin Nano에서 ROS2 + Docker 사용**
4. **Windows에서 개발한 프로그램을 Linux 서버에 배포**

목적에 따라 설치 방법과 Docker 구성 방법이 달라집니다.