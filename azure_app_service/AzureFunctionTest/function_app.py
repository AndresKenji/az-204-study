import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="helloapp")
def http_trigger1(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hola, {name}. Este disparador HTTP ha ejecutado la funcion satisfactoriamente.")
    else:
        return func.HttpResponse(
             "Esta función activada por HTTP ha sido ejecutada correctamente. Pasa el valor name en el query string o en el cuerpo de la petición para una respuesta personalizada.",
             status_code=200
        )

@app.timer_trigger(schedule="0 */12 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def cronapp(myTimer: func.TimerRequest) -> None:
    
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function executed.')