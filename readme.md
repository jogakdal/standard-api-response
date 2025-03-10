# 프로젝트 다운로드 
이 프로젝트의 전체 소스 코드를 다운 받으시려면 저장소를 클론하고 필요한 종속성을 설치하십시오:

```sh
git clone https://github.com/jogakdal/standard-api-response.git
cd <repository-directory>
pip install -r requirements.txt
```

## pypl 등록
각 패키지 디렉토리에서 다음 명령 수행.
```sh
python setup.py sdist bdist_wheel
pip install twine
twine check dist/*. # for check
twine upload dist/*
```

