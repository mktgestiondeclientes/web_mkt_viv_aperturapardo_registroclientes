from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.cloud import bigquery
import datetime

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = bigquery.Client()

PROJECT_ID = "spsa-marketing-prd"
DATASET_ID = "GDC_proyectos"
# <-- CORRECCIÓN: He añadido el '0' que faltaba en los nombres de las tablas
TABLE = "tb_mkt_dim_viv_registrowebpardo"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    promotor = request.query_params.get("promotor", "")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "promotor": promotor
        }
    )

@app.post("/verify", response_class=HTMLResponse)
async def verify_person(
    request: Request,
    tipo_documento: str = Form(...),
    id_documento: str = Form(...),
    apellido_paterno: str = Form(...),
    promotor: str = Form("")
):
    ape_paterno_norm = apellido_paterno.strip().upper()

    query = f"""
        SELECT
            tipo_documento_detalle,
            numero_documento,
            Nombres,
            apellido_paterno,
            apellido_materno,
            celular,
            email,
            fecha_nacimiento,
            distrito,
            tipo_via,
            nombre_via,
            numero_dom,
            numero_lote
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE}`
        WHERE tipo_documento_detalle = @tipo
          AND numero_documento = @id
          AND UPPER(TRIM(apellido_paterno)) = @ape_paterno
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("tipo", "STRING", tipo_documento),
            bigquery.ScalarQueryParameter("id", "STRING", id_documento),
            bigquery.ScalarQueryParameter("ape_paterno", "STRING", ape_paterno_norm),
        ]
    )
    query_job = client.query(query, job_config=job_config)
    results = list(query_job)
    print(f"Resultados encontrados: {len(results)}")
    context = {
        "request": request,
        "tipo_documento": tipo_documento,
        "id_documento": id_documento,
        "apellido_paterno": apellido_paterno,       
        "persona": results[0] if results else None,
        "promotor": promotor
    }
    
    return templates.TemplateResponse(
    request=request,
    name="register.html",
    context=context
)

@app.post("/register", response_class=HTMLResponse)
async def register_event(
    request: Request,
    tipo_documento: str = Form(...),
    id_documento: str = Form(...),
    nombres: str = Form(...),
    apellido_paterno: str = Form(...),
    apellido_materno: str = Form(...),
    estado_civil: str = Form(...),
    celular: str = Form(...),
    email: str = Form(...),
    fecha_nacimiento: str = Form(...),
    flg_hijos: str = Form(...),
    distrito: str = Form(...),
    tipo_via: str = Form(...),
    nombre_via: str = Form(...),
    numero_dom: str = Form(""),
    numero_lote: str = Form(""),
    acepta_terminos: bool = Form(False),
    acepta_politicas: bool = Form(False),
    acepta_comunicaciones: bool = Form(False),
    promotor: str = Form("")
):

    client_ip = request.client.host
    user_agent_string = request.headers.get("user-agent", "No especificado")

    # ✅ AQUÍ VAN LAS VARIABLES
    terminos_version = "v29sep2025"
    politicas_version = "v29sep2025"
    terceros_version = "v29sep2025"    

    query = f"""
    MERGE `{PROJECT_ID}.{DATASET_ID}.{TABLE}` T
    USING (
        SELECT
            @tipo AS TIPO_DOCUMENTO_DETALLE,
            @id AS NUMERO_DOCUMENTO,
            @nombres AS NOMBRES,
            @ape_paterno AS APELLIDO_PATERNO,
            @ape_materno AS APELLIDO_MATERNO,
            @estado_civil AS ESTADO_CIVIL,
            @celular AS CELULAR,
            @email AS EMAIL,
            @fecha_nacimiento AS FECHA_NACIMIENTO,
            @flg_hijos AS FLG_HIJOS,
            @distrito AS DISTRITO,
            @tipo_via AS TIPO_VIA,
            @nombre_via AS NOMBRE_VIA,
            @numero_dom AS NUMERO_DOM,
            @numero_lote AS NUMERO_LOTE,
            @terminos AS ACEPTA_TERMINOS,
            @politicas AS ACEPTA_POLITICAS,
            @comunicaciones AS ACEPTA_COMUNICACIONES,
            @fecha AS FECHA_INSCRIPCION,
            @ip AS IP_ADDRESS,
            @ua AS USER_AGENT,
            @v1 AS VERSION_TERMINOS,
            @v2 AS VERSION_POLITICAS,
            @v3 AS VERSION_TERCEROS,
            @registrado AS REGISTRADO,
            @promotor AS PROMOTOR
    ) S
    ON T.NUMERO_DOCUMENTO = S.NUMERO_DOCUMENTO

    WHEN MATCHED THEN
      UPDATE SET
        NOMBRES = S.NOMBRES,
        APELLIDO_PATERNO = S.APELLIDO_PATERNO,
        APELLIDO_MATERNO = S.APELLIDO_MATERNO,
        ESTADO_CIVIL = S.ESTADO_CIVIL,
        CELULAR = S.CELULAR,
        EMAIL = S.EMAIL,
        FECHA_NACIMIENTO = S.FECHA_NACIMIENTO,
        FLG_HIJOS = S.FLG_HIJOS,
        DISTRITO = S.DISTRITO,
        TIPO_VIA = S.TIPO_VIA,
        NOMBRE_VIA = S.NOMBRE_VIA,
        NUMERO_DOM = S.NUMERO_DOM,
        NUMERO_LOTE = S.NUMERO_LOTE,
        ACEPTA_TERMINOS = S.ACEPTA_TERMINOS,
        ACEPTA_POLITICAS = S.ACEPTA_POLITICAS,
        ACEPTA_COMUNICACIONES = S.ACEPTA_COMUNICACIONES,
        FECHA_INSCRIPCION = S.FECHA_INSCRIPCION,
        IP_ADDRESS = S.IP_ADDRESS,
        USER_AGENT = S.USER_AGENT,
        VERSION_TERMINOS = S.VERSION_TERMINOS,
        VERSION_POLITICAS = S.VERSION_POLITICAS,
        VERSION_TERCEROS = S.VERSION_TERCEROS,
        REGISTRADO = S.REGISTRADO,
        PROMOTOR = S.PROMOTOR

    WHEN NOT MATCHED THEN
      INSERT (
        TIPO_DOCUMENTO_DETALLE,
        NUMERO_DOCUMENTO,
        NOMBRES,
        APELLIDO_PATERNO,
        APELLIDO_MATERNO,
        ESTADO_CIVIL,
        CELULAR,
        EMAIL,
        FECHA_NACIMIENTO,
        FLG_HIJOS,
        DISTRITO,
        TIPO_VIA,
        NOMBRE_VIA,
        NUMERO_DOM,
        NUMERO_LOTE,
        ACEPTA_TERMINOS,
        ACEPTA_POLITICAS,
        ACEPTA_COMUNICACIONES,
        FECHA_INSCRIPCION,
        IP_ADDRESS,
        USER_AGENT,
        VERSION_TERMINOS,
        VERSION_POLITICAS,
        VERSION_TERCEROS,
        REGISTRADO,
        PROMOTOR
      )
      VALUES (
        S.TIPO_DOCUMENTO_DETALLE,
        S.NUMERO_DOCUMENTO,
        S.NOMBRES,
        S.APELLIDO_PATERNO,
        S.APELLIDO_MATERNO,
        S.ESTADO_CIVIL,
        S.CELULAR,
        S.EMAIL,
        S.FECHA_NACIMIENTO,
        S.FLG_HIJOS,
        S.DISTRITO,
        S.TIPO_VIA,
        S.NOMBRE_VIA,
        S.NUMERO_DOM,
        S.NUMERO_LOTE,
        S.ACEPTA_TERMINOS,
        S.ACEPTA_POLITICAS,
        S.ACEPTA_COMUNICACIONES,
        S.FECHA_INSCRIPCION,
        S.IP_ADDRESS,
        S.USER_AGENT,
        S.VERSION_TERMINOS,
        S.VERSION_POLITICAS,
        S.VERSION_TERCEROS,
        TRUE,
        S.PROMOTOR
      )
    """

    job = client.query(query, job_config=bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("tipo", "STRING", tipo_documento),
            bigquery.ScalarQueryParameter("id", "STRING", id_documento),
            bigquery.ScalarQueryParameter("nombres", "STRING", nombres.upper()),
            bigquery.ScalarQueryParameter("ape_paterno", "STRING", apellido_paterno.upper()),
            bigquery.ScalarQueryParameter("ape_materno", "STRING", apellido_materno.upper()),
            bigquery.ScalarQueryParameter("estado_civil", "STRING", apellido_materno.upper()),
            bigquery.ScalarQueryParameter("celular", "STRING", celular),
            bigquery.ScalarQueryParameter("email", "STRING", email.upper()),
            bigquery.ScalarQueryParameter("fecha_nacimiento", "DATE", fecha_nacimiento.upper()),
            bigquery.ScalarQueryParameter("flg_hijos", "STRING", flg_hijos),
            bigquery.ScalarQueryParameter("distrito", "STRING", distrito.upper()),
            bigquery.ScalarQueryParameter("tipo_via", "STRING", tipo_via.upper()),
            bigquery.ScalarQueryParameter("nombre_via", "STRING", nombre_via.upper()),
            bigquery.ScalarQueryParameter("numero_dom", "STRING", numero_dom.upper()),
            bigquery.ScalarQueryParameter("numero_lote", "STRING", numero_lote.upper()),
            bigquery.ScalarQueryParameter("terminos", "BOOL", acepta_terminos),
            bigquery.ScalarQueryParameter("politicas", "BOOL", acepta_politicas),
            bigquery.ScalarQueryParameter("comunicaciones", "BOOL", acepta_comunicaciones),
            bigquery.ScalarQueryParameter("fecha", "TIMESTAMP", datetime.datetime.utcnow()),
            bigquery.ScalarQueryParameter("ip", "STRING", client_ip),
            bigquery.ScalarQueryParameter("ua", "STRING", user_agent_string),
            bigquery.ScalarQueryParameter("v1", "STRING", terminos_version),
            bigquery.ScalarQueryParameter("v2", "STRING", politicas_version),
            bigquery.ScalarQueryParameter("v3", "STRING", terceros_version),
            bigquery.ScalarQueryParameter("registrado","BOOL",True),
            bigquery.ScalarQueryParameter("promotor","STRING",promotor.upper())
        ]
    ))

    job.result()

    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
            "request": request,
            "nombres": nombres
        }
    )
    #prueba en could build