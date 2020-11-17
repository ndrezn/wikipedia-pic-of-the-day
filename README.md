# Wikipedia Picture of the Day

<p align="center">
    <img src="example.png", width=500>
</p>

Posts the picture of the day from Wikipedia daily to Twitter from [@wiki_potd](https://twitter.com/wiki_potd). Based on the community sourced [Wikipedia Picture of the Day](https://en.m.wikipedia.org/wiki/Wikipedia:Picture_of_the_day).

Also powers a sibling account [@potd_context](https://twitter.com/potd_context), which posts article titles, links, and extra captioning.

## Instructions
Note that correct API keys are required.

**To run with bash (instant)**
```
bash run.sh
```
**To run with Docker (scheduled)**

Build the container
```
docker build -t wiki-bot .
```
Run the container in detached mode
```
docker run --env-file .env -d wiki-bot
```
