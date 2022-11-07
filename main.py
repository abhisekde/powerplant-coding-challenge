from fastapi import FastAPI, HTTPException, status
import uvicorn
import logging
from meritplan import MeritPlan

app = FastAPI(title='Power production plan')

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
    )

@app.get('/')
def index():
    return app.title

@app.post('/productionplan')
def productionplan(demand: dict):

    plan = None

    try:
        plan = MeritPlan(demand)
        logging.info(f'Power plants \n{plan.power_plants}')
    except Exception as ex:
        logging.error(ex.__str__())
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail='Request body validation failed'
        )

    try:
        result = plan.calculate()
        return result
    except Exception as ex:
        logging.error('Calcualtion of unit commitment failed')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail='Calcualtion of unit commitment failed'
        )
    


if __name__ == '__main__':
    port = 8888
    try:
        logging.info(f'Starting {app.title} on port {port}')
        uvicorn.run(app=app, port=port, host='0.0.0.0')
    except Exception as ex:
        logging.error(f'Aborted. {app.title} crashed on startup', exc_info=ex)
