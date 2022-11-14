# powerplant-coding-challenge
### Solution by **Abhisek De**
#### abhisek.de@capgemini.ccom
<br>

## Requirements
- Python 3
- Docker Desktop
- pandas
- uvicorn
- fastapi

<br>

## Installation
### Local environment
`pip install -r requirements.txt`

### Docker container
`docker build -t engie-uc .`

<br>

## Execution
### Local environment
`python main.py`

### Debugging
`source powerplant/Scripts/activate`

`uvicorn main:app --port 8888`

### Docker container
`docker run -p 8888:8888 engie-uc`

<br>

## API Response
`curl -X POST -H 'Content-Type: application/json' -d @powerplant.data http://127.0.0.1:8888/productionplan`

Where the file `powerplant.data` contains powerplant information in JSON format

<br>

## Algorithm
Calculate the net price by cnsidering the fuel efficiency 

Calculate the power production price/MWH as per the net efficiency

Calculate the CO2 allowance/MWH where applicable

Total cost/MWH of production = net price + CO2 allowance

Order the powerplants by economy of price ascending, capacity decreasing

Make unit comitments as per the demand from the the ordered list

This will endure that the power is produced at minimal cost untill demand is met

Return the result
