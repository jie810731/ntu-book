## how to build

```
docker build -t ntu .
```

## how to run

```
docker run -i -t \
    -v "$PWD":/app \
    -e ACCOUNT='' \
    -e PASSWORD='' \
    -e BOOK_DATE='YYYY-MM-DD' \
    -e START_BOOK_TIME='HH' \
    -e END_BOOK_TIME='HH' \
    -e PLACE_NUMBER=1 \
   --name ntu_container ntu
```
