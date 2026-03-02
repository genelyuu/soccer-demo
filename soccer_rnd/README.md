# Fatigue–HRV–Load PoV Repository

Dataset-centric EDA and statistics-first PoV for ATL/CTL/ACWR.

## 환경 설정

### 가상환경 생성 및 패키지 설치

1. **가상환경 생성** (프로젝트 루트에서 실행):
   ```bash
   python -m venv venv
   ```

2. **가상환경 활성화**:
   - Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - Windows (CMD):
     ```cmd
     venv\Scripts\activate.bat
     ```
   - Linux/macOS:
     ```bash
     source venv/bin/activate
     ```

3. **패키지 설치**:
   ```bash
   pip install -r requirements.txt
   ```

### Jupyter 노트북 가상환경 설정

1. **가상환경 활성화 후 ipykernel 등록**:
   ```bash
   python -m ipykernel install --user --name=soccer_rnd --display-name "Python (soccer_rnd)"
   ```

2. **Jupyter 노트북 실행**:
   ```bash
   jupyter notebook
   ```

3. **노트북에서 커널 선택**:
   - 노트북 실행 후 상단 메뉴: `Kernel` → `Change Kernel` → `Python (soccer_rnd)` 선택

### 테스트 실행

```bash
python -m pytest tests/ -v
```

## 프로젝트 구조

자세한 내용은 [`docs/README.md`](docs/README.md)를 참조하세요.
