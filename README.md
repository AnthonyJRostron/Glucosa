# README — Diario de Diabetes

---

> ## ⚠️ AVISO IMPORTANTE — LEE ESTO ANTES DE USAR LA APP
>
> **Esta aplicación NO diagnostica, NO prescribe y NO recomienda tratamientos de insulina ni de ningún otro fármaco.**
>
> La app es únicamente una **herramienta de registro y visualización** de los datos que tú introduces. **Solo un profesional sanitario cualificado** (endocrino, educador en diabetes, enfermería especializada o médico de familia) puede diagnosticar, ajustar dosis, cambiar pautas o recomendar tratamientos.
>
> **Esta app debe haberte sido facilitada por una clínica o unidad de diabetes acreditada.** Esa clínica tiene acceso a herramientas adicionales para **revisar y corregir tus datos** (por ejemplo, si olvidaste registrar un medicamento, si una dosis quedó mal anotada o si un ajuste de pauta no se reflejó correctamente). No dudes en ponerte en contacto con ella para cualquier corrección.
>
> **Nunca modifiques tu tratamiento por tu cuenta basándote únicamente en lo que veas en la app.** Si tienes dudas sobre tus glucemias, tus dosis o tus patrones, contacta con tu equipo de diabetes.
>
> **Se recomienda volver a la consulta con la periodicidad que te indique tu equipo sanitario.** Como orientación general, la mayoría de guías clínicas recomiendan **revisión cada 3 meses** para personas con diabetes tipo 1 o tipo 2 insulinizadas, y **cada 6–12 meses** para personas con diabetes tipo 2 no insulinizadas o bien controladas. **La frecuencia exacta la decide tu profesional sanitario.** Lleva siempre el informe PDF o el archivo JSON de la app a cada revisión.

---

## Índice

1. [Descripción general](#1-descripción-general)
2. [Inicio rápido para pacientes](#2-inicio-rápido-para-pacientes)
3. [Requisitos técnicos](#3-requisitos-técnicos)
4. [Primera configuración: qué debe introducir el paciente](#4-primera-configuración-qué-debe-introducir-el-paciente)
5. [Panel de configuración colapsable](#5-panel-de-configuración-colapsable)
6. [Cómo añadir, editar y eliminar registros](#6-cómo-añadir-editar-y-eliminar-registros)
7. [Sistemas que garantizan la correcta introducción de datos](#7-sistemas-que-garantizan-la-correcta-introducción-de-datos)
8. [Explicación detallada de cada sección](#8-explicación-detallada-de-cada-sección)
9. [Para profesionales sanitarios: datos de ejemplo (diabetes.json)](#9-para-profesionales-sanitarios-datos-de-ejemplo-diabetesjson)
10. [Privacidad, seguridad y cumplimiento](#10-privacidad-seguridad-y-cumplimiento)
11. [Preguntas frecuentes (FAQ)](#11-preguntas-frecuentes-faq)
12. [Solución de problemas](#12-solución-de-problemas)
13. [Glosario](#13-glosario)
14. [Anexo A: esquema del archivo JSON](#14-anexo-a-esquema-del-archivo-json)
15. [Anexo B: valores admitidos en campos cerrados](#15-anexo-b-valores-admitidos-en-campos-cerrados)

---

## 1. Descripción general

**Diario de Diabetes** es una aplicación autocontenida en un único archivo, sin instalación y sin servidor. Todos los datos que introduces se guardan **localmente en tu propio navegador** y puedes exportarlos o importarlos como un archivo \`.json\`.

La app permite a una persona con diabetes:

- **Registrar cada día** sus glucemias (antes y después de las comidas y por la noche).
- **Registrar la insulina** u otros medicamentos que se inyecta o toma, con dosis, unidad, hora, si la ha omitido y una nota.
- **Anotar el ejercicio** realizado (tipo y duración), el **estado de ánimo** y el **contexto dietético** de cada jornada.
- **Recibir automáticamente** los datos meteorológicos de su localidad (temperatura, humedad, precipitación, presión y viento), que se guardan junto al registro porque influyen en el control glucémico.
- **Consultar resúmenes y estadísticas** de los últimos días, semanas o meses.
- **Generar informes PDF** totalmente configurables para llevar a la consulta.
- **Enviar por correo** a la clínica el archivo JSON con sus datos, antes de la consulta.

La app también está pensada para que **profesionales sanitarios** (endocrinólogos, educadores en diabetes, enfermería, médicos de familia) puedan revisar informes de sus pacientes, comparar tendencias y demostrar el funcionamiento de la herramienta con **datos de ejemplo realistas** incluidos en el archivo \`diabetes.json\`.

> Recuerda el aviso del principio: **la app no diagnostica ni recomienda tratamientos**. Solo un profesional sanitario puede hacerlo, y solo la clínica que te proporcionó la app puede corregir tus datos si detectas errores.

---

## 2. Inicio rápido para pacientes

**Al arrancar la app por primera vez verás dos opciones claras:**

- **Descargar datos de ejemplo** (para que explores cómo funciona la app con información ya rellena).
- **Añadir un nuevo paciente** (para empezar tu propio diario desde cero).

### 2.1 Ruta A — Solo quiero ver cómo funciona

1. Pulsa **"Descargar datos de ejemplo"**.
2. La app carga **automáticamente** el archivo \`diabetes.json\` incluido con la aplicación: **no tienes que buscarlo ni seleccionarlo manualmente**.
3. La app carga cinco pacientes de ejemplo con un año completo de registros.
4. Explora los registros, los informes PDF y las gráficas.
5. Cuando quieras empezar tu propio diario, elimina los datos de ejemplo (o crea tu propio paciente y trabaja en paralelo).

### 2.2 Ruta B — Quiero crear mi propio diario

1. Pulsa **"Añadir un nuevo paciente"**.
2. Rellena tus **datos personales y clínicos** (nombre, fecha de nacimiento, tipo de diabetes…).
3. Añade tus **medicamentos** con la **dosis habitual** y la **hora habitual**.
4. Indica tu **localidad** para que la app descargue la meteorología.
5. Empieza a registrar glucemias e insulina.

### 2.3 Ruta C — Soy profesional sanitario y quiero cargar el ejemplo clínico

1. Pulsa **"Descargar datos de ejemplo"**.
2. La app carga **automáticamente** el archivo \`diabetes.json\`: no hay que seleccionar ningún archivo ni buscarlo en el dispositivo.
3. La app carga los cinco pacientes de ejemplo con sus 365 registros cada uno.

### 2.4 Cómo llevar los datos a la consulta (lo más importante)

Cuando vayas a la consulta, **tienes tres formas de entregar tus datos** al profesional sanitario, de la más recomendable a la menos:

1. **Recomendado — Enviar el correo desde la app.** Pulsa el botón de **"Enviar por correo"**. La app:
   - Genera un **archivo JSON** con todos tus datos.
   - Lo **guarda automáticamente en el directorio de descargas por defecto** de tu dispositivo (carpeta **Descargas** en la mayoría de sistemas; puede variar según el navegador y el sistema operativo).
   - Abre tu cliente de correo con la dirección de la clínica ya puesta y el archivo JSON adjunto.
   - Puedes **enviarlo directamente a la clínica** antes de la consulta, para que el profesional lo revise con antelación.
2. **Alternativa — Generar y llevar el PDF impreso.** El PDF es suficiente para una revisión rápida. Puedes generarlo desde el botón **"Informe PDF"** y, si quieres, imprimirlo o guardarlo manualmente.
3. **Alternativa — Llevar el JSON en un pendrive o en el propio dispositivo.** El JSON contiene **todos** los datos (incluidos los que no caben en el PDF), y la clínica puede cargarlo en sus herramientas para una revisión más profunda.

> **¿Dónde se guardan los archivos exportados?** Todos los archivos que la app descarga (el JSON al enviar el correo y el JSON al usar **Exportar Pacientes**) se guardan en el **directorio de descargas por defecto** del dispositivo, que habitualmente es la carpeta **Descargas**. El PDF, en cambio, se genera en el navegador y solo se guarda si tú lo indicas en el diálogo de impresión/guardado.

> **Consejo:** envía el correo **al menos 24–48 horas antes** de la consulta. Así el profesional puede revisar tus datos con calma y aprovechar mejor el tiempo de visita.

### 2.5 ¿Con qué frecuencia debo exportar mis datos?

**Exporta tus datos al menos una vez a la semana.** La app guarda los datos en el navegador, y un borrado accidental, un cambio de dispositivo o una limpieza del navegador pueden hacerte perderlo todo. Exportar semanalmente es una red de seguridad sencilla.

> **Importante:** exportar no es lo mismo que enviar el correo a la clínica. Exportar es una **copia de seguridad personal**; enviar el correo es **compartir con el profesional sanitario** para la consulta.

---

## 3. Requisitos técnicos

### 3.1 Requisitos del dispositivo

| Elemento | Mínimo recomendado |
|---|---|
| Navegador | Chrome / Edge 100+, Firefox 100+, Safari 15+ |
| Sistema operativo | Windows 10+, macOS 12+, Linux, Android 9+, iOS 15+ |
| Memoria RAM | 2 GB |
| Almacenamiento libre | ≥ 50 MB |
| **Conexión a internet** | **Necesaria para las librerías de terceros que dibujan las gráficas y que exportan el PDF** |
| JavaScript | Activado (imprescindible) |

### 3.2 Requisitos funcionales

- **No requiere instalación**.
- **Requiere conexión a internet** para:
  - Cargar las **librerías de terceros** que dibujan las **gráficas**.
  - Cargar las **librerías de terceros** que generan la **exportación a PDF**.
  - Descargar la **meteorología** (si tienes ubicación configurada).
- **No requiere registro ni contraseña.**
- **Compatible con exportación**: puedes descargar todo el diario como archivo \`.json\`.
- **Generación de PDF en cliente**: el PDF se crea en tu navegador; los datos no se envían a ningún servidor salvo que tú decidas enviarlos por correo desde la app.

### 3.3 Limitaciones conocidas

- **Sin internet, las gráficas y el PDF no funcionan.** El registro de glucemias e insulina sí funciona sin conexión, pero no podrás visualizar gráficas ni generar PDF hasta que recuperes la conexión.
- El **almacenamiento local** está vinculado al navegador y al dispositivo. Si borras los datos del navegador, pierdes el diario. **Exporta semanalmente.**
- El **modo incógnito** no conserva los datos al cerrar la ventana.
- La **meteorología** requiere conexión en el momento de consultar; si no hay conexión, el registro se guarda con los campos meteorológicos vacíos.
- Los **PDF** se generan con el motor de impresión del navegador. Si el PDF sale con saltos raros, revisa los márgenes de impresión.

---

## 4. Primera configuración: qué debe introducir el paciente

La primera vez que se abre la app, el diario está vacío. Antes de registrar nada conviene rellenar los datos de configuración. Todos estos campos se usan luego para validar los registros, calcular la severidad y construir los informes.

### 4.1 Datos personales y clínicos

| Campo | Obligatorio | Descripción | Ejemplo |
|---|---|---|---|
| **Nombre completo** | Sí | Nombre y apellidos del paciente. Aparece en los informes. | \`Javier Manuel Ortega Díaz\` |
| **DNI / Identificador** | Recomendado | Documento de identidad o número de historia clínica. | \`12345678Z\` |
| **Número de la Seguridad Social (NUSS)** | Opcional | Número de afiliación a la Seguridad Social. Formato habitual en España: **12 dígitos** (2 de provincia + 8 del número + 2 de control), a menudo escrito con barras y guiones: \`28/12345678-90\`. | \`28/12345678-90\` |
| **Sexo** | Sí | \`Hombre\`, \`Mujer\` o \`Sin especificar\`. Condiciona las opciones de embarazo. | \`male\` |
| **Fecha de nacimiento** | Sí | Determina si el paciente es niño/adolescente o adulto, y permite calcular la edad. | \`1985-04-10\` |
| **Tipo de diabetes** | Sí | \`Tipo 1\`, \`Tipo 2\` o \`Gestacional\`. | \`type1\` |
| **Grupo de paciente** | Sí | \`Adulto\`, \`Niño/adolescente\` o \`Embarazo\`. | \`adult\` |
| **Estado de embarazo** | Solo mujeres | \`No embarazada\`, \`Embarazada\`, \`Lactancia\` o \`Postparto\`. | \`not_pregnant\` |

> **Nota sobre la categoría de embarazo:** la **categoría de embarazo** (primer, segundo o tercer trimestre) **no se registra en la app**. Si tu profesional sanitario necesita esa información, la manejará en la clínica con sus propias herramientas.

> **Nota sobre el objetivo personalizado:** el campo **Objetivo personalizado** (rango de glucemia objetivo distinto del estándar) **no lo rellena el paciente**. Lo establece el **profesional sanitario** de la clínica que le proporcionó la app. Si tu endocrino te ha dado un objetivo distinto del estándar, será él quien lo introduzca en la app o en sus herramientas clínicas.

### 4.2 Unidades de glucosa y objetivos

- **Unidad de glucosa**: elige \`mg/dL\` (habitual en España, Estados Unidos y Latinoamérica) o \`mmol/L\` (habitual en Reino Unido y algunos países europeos). Todos los valores introducidos a partir de ese momento se interpretarán y mostrarán en esa unidad. Si cambias de unidad más adelante, la app convierte automáticamente los valores ya guardados.
- **Objetivos por defecto**:
  - Adulto no embarazado: **70–180 mg/dL** (3,9–10,0 mmol/L).
  - Embarazo: **63–140 mg/dL** (3,5–7,8 mmol/L).
  - Niños/adolescentes: **70–180 mg/dL** con ajustes según edad.
- Si tu profesional sanitario te ha dado un objetivo distinto, **será él quien lo introduzca** en la app o en sus herramientas clínicas. El paciente no debe modificar este campo por su cuenta.

### 4.3 Medicamentos e insulina

En la sección de **Medicamentos** se añaden los fármacos que el paciente usa habitualmente. Cada medicamento tiene estos campos:

| Campo | Descripción | Ejemplo |
|---|---|---|
| **Nombre comercial** | Denominación tal como aparece en el envase. | \`ABASAGLAR 100 UNIDADES/ML KWIKPEN SOLUCION INYECTABLE EN PLUMA PRECARGADA\` |
| **Principio activo** | Fármaco real. | \`Insulina glargina\` |
| **Laboratorio** | Titular del medicamento. | \`Eli Lilly Nederland B.V.\` |
| **Clase** | Clasificación ATC. | \`Insulinas y analogos de accion prolongada (A10AE04)\` |
| **Vía de administración** | Subcutánea, oral, etc. | \`Subcutanea\` |
| **Unidad** | Unidad de medida (UI, mg, mcg…). | \`UI\` |
| **Riesgo de hipoglucemia** | Marca si el fármaco puede provocar hipoglucemias. | \`false\` para análogos basales, \`true\` para insulina rápida |
| **Fuente** | Origen del dato (CIMA, manual…). | \`cima\` |
| **Dosis predeterminada** | Dosis que la app propondrá por defecto al registrar. | \`16\` |
| **Unidad predeterminada** | Unidad que se mostrará por defecto. | \`ui\` |
| **Posibles dosis** | Lista de presentaciones disponibles. | \`[{ valor: "100", unidad: "U" }]\` |

### 4.4 Dosis habitual y hora habitual

En cada medicamento debes indicar **dos cosas clave**:

1. **Dosis habitual**: la dosis que el paciente suele administrarse. La app la usará como valor por defecto al abrir el formulario de nueva dosis y como referencia para avisar si un registro se aleja mucho de lo habitual.
2. **Hora habitual**: la hora a la que suele administrarse. La app la usará para:
   - Ordenar los registros y agruparlos por "toma de mañana / mediodía / tarde / noche".
   - Avisar si una dosis no se ha registrado en las horas siguientes a la hora habitual.
   - Dibujar correctamente las gráficas de "insulina a lo largo del día".

> **Ejemplo**: una persona que se pone 16 UI de insulina glargina a las 21:00 tendría \`dosisPredeterminada: "16"\` y hora habitual \`21:00\`.

### 4.5 Ubicación para la meteorología

Indica la **ciudad y el país** donde vives habitualmente (por ejemplo, \`Vigo, Pontevedra\` o \`Barcelona, España\`). La app usará esa ubicación para:

- Descargar automáticamente la **temperatura, humedad, precipitación, presión atmosférica y viento** del día de cada registro.
- Guardar el nombre de la localidad junto al registro (útil si viajas: los registros de viaje conservarán la localidad de destino).
- Permitir análisis posteriores (por ejemplo, ¿empeora el control cuando llueve o hace mucho calor?).

> **Consejo**: si te vas de viaje, puedes cambiar temporalmente la ubicación. La app guardará los registros nuevos con la nueva localidad y conservará los antiguos con la suya.

---

## 5. Panel de configuración colapsable

Una vez completada la primera configuración, el panel deja de ser necesario en el día a día. Por eso la aplicación lo **colapsa automáticamente**:

- En la parte superior de la pantalla principal verás un **resumen compacto** con tu nombre, edad, tipo de diabetes y número de medicamentos activos.
- Para **desplegar** la configuración completa, **pulsa directamente sobre la barra del resumen**. Es decir, la barra entera es el botón: no hay que buscar ningún icono concreto.
- Para **volver a colapsarla**, vuelve a **pulsar sobre la barra**.

Esto evita que la pantalla se llene de campos que solo se rellenan una vez y deja más espacio para el registro diario, que es lo que realmente se usa cada día.

> **Importante**: los datos de configuración **no se pierden** al colapsar el panel. Solo se ocultan visualmente. Si necesitas cambiar algo, pulsa sobre la barra, edita, y vuelve a pulsar sobre la barra para colapsar.

---

## 6. Cómo añadir, editar y eliminar registros

La aplicación distingue **dos grandes tipos de registro**:

1. **Registros de glucemia** (\`records\`): recogen las glucemias del día y el contexto (comida, ejercicio, ánimo, meteorología…).
2. **Registros de medicación** (\`medicationLog\`): recogen cada dosis de insulina u otro fármaco administrada (u omitida).

### 6.1 Registro diario de glucemia

Para crear un registro:

1. Pulsa **"Nuevo registro"**.
2. Se abrirá un formulario con:
   - **Fecha** (por defecto, hoy).
   - **Comida** a la que corresponde el registro: \`Desayuno\`, \`Comida\`, \`Cena\`, \`Recena\` u \`Otro\`.
   - **Glucemia antes** de la comida.
   - **Glucemia después** de la comida (opcional).
   - **Glucemia nocturna** (opcional).
   - **Ejercicio**: tipo (\`Caminar\`, \`Bici\`, \`Natación\`, \`Correr\`, \`Otro\`) y duración en minutos.
   - **Estado de ánimo**: uno o varios de \`Normal\`, \`Estresado\`, \`Ansioso\`, \`Cansado\`, \`Fatiga\`.
   - **Contexto dietético**: uno o varios de \`Plan recomendado\`, \`Comida familiar\`, \`Exceso de cantidad\`, \`Alcohol\`, \`Salté una comida\`, \`Comida rápida\`, \`Restaurante\`, \`Evento especial\`, \`Comida de trabajo\`, \`Otro imprevisto\`.
   - **Comentarios** libres.
   - **Severidad** (se calcula automáticamente, ver §7.4).
   - **Meteorología**: se rellena sola si tienes ubicación configurada y conexión.
3. Pulsa **"Guardar"**. El registro aparece inmediatamente en la lista cronológica.

### 6.2 Registro de medicación / inyecciones

Para registrar una dosis:

1. Pulsa **"Nueva dosis"** o el botón rápido del medicamento correspondiente.
2. Se abrirá un formulario con:
   - **Medicamento** (ya preseleccionado si usas el botón rápido).
   - **Dosis** (por defecto, la dosis habitual configurada).
   - **Unidad** (UI, mg…).
   - **Fecha y hora** (por defecto, ahora).
   - **Omitida**: marca esta casilla si **no** te has puesto la dosis (olvido, decisión médica, etc.).
   - **Nota**: campo libre para explicar el motivo.
3. Pulsa **"Guardar"**.

> La casilla **Omitida** es importante: permite distinguir "no me puse la insulina" de "no registré la dosis". En los informes se muestran como eventos distintos.

### 6.3 Edición y borrado

- **Editar**: pulsa sobre cualquier registro de la lista. Se abrirá el formulario con los datos cargados.
- **Eliminar**: dentro del formulario de edición, pulsa **"Eliminar"**. La app pedirá confirmación antes de borrar.
- **Deshacer**: si acabas de borrar un registro, aparece un aviso con **"Deshacer"** durante unos segundos.

> **Recuerda:** si detectas que te falta un medicamento, que una dosis está mal anotada o que un ajuste de pauta no se reflejó, contacta con tu clínica. Ellos tienen herramientas para corregir tus datos de forma segura.

---

## 7. Sistemas que garantizan la correcta introducción de datos

### 7.1 Validación en el momento de la entrada

La app aplica validaciones **mientras escribes**, no solo al guardar:

| Campo | Validación |
|---|---|
| Fecha | Debe ser una fecha válida y no puede ser futura (salvo confirmación expresa). |
| Glucemia | Debe ser un número. En mg/dL se aceptan valores de 10 a 800; en mmol/L, de 0,5 a 45. Fuera de ese rango la app avisa y pide confirmación. |
| Dosis | Debe ser un número positivo. Si se aleja más de un 50 % de la dosis habitual, la app avisa. |
| Hora | Formato de 24 horas. |
| Unidad | Selector cerrado. |
| Tipo de ejercicio | Selector cerrado. |
| Estado de ánimo | Lista cerrada con selección múltiple. |
| Contexto dietético | Lista cerrada con selección múltiple. |
| Comentarios | Texto libre, longitud máxima 500 caracteres. |

### 7.2 Gestión de valores ausentes

- **Glucemia después** y **glucemia nocturna** son opcionales. Se guardan como \`null\` y **no cuentan como cero** en las estadísticas.
- **Ejercicio** puede quedar vacío.
- **Meteorología**: si no hay conexión o no hay ubicación configurada, los campos quedan vacíos, pero el registro se guarda.
- **Estado de ánimo**, **contexto dietético**: listas vacías si no se selecciona nada.
- **Comentarios**: cadena vacía si no se escriben.

Reglas estadísticas:

- Los **valores \`null\` se excluyen** de medias, medianas, percentiles y desviaciones estándar.
- En los gráficos, los huecos se representan como **ausencia de punto**, no como cero.
- En los informes PDF se indica el **número de valores disponibles** sobre el total de días del período.

### 7.3 Detección de duplicados y coherencia temporal

- La app **avisa** si intentas guardar dos registros con la misma fecha, misma comida y misma glucemia antes.
- Si detecta dos **dosis del mismo medicamento** en menos de 4 horas, muestra un aviso.
- Si la **fecha del registro** es anterior a la fecha de nacimiento o posterior a hoy, se bloquea.
- Si un registro tiene **glucemia después** pero no **glucemia antes**, la app permite guardarlo pero lo marca como **incompleto** en los informes.

### 7.4 Cálculo automático de severidad

| Severidad | Criterio orientativo |
|---|---|
| \`null\` | Glucemia dentro de objetivos y sin síntomas. |
| \`mild\` | Glucemia ligeramente fuera de rango (180–250 mg/dL en ayunas, o 55–70 mg/dL). |
| \`moderate\` | Glucemia claramente fuera de rango (> 250 mg/dL o 40–54 mg/dL). |
| \`urgent\` | Glucemia muy fuera de rango (> 300 mg/dL o < 40 mg/dL). |
| \`emergency\` | Glucemia extrema con riesgo vital (< 30 mg/dL, > 400 mg/dL o pérdida de conciencia). |
| \`severe\` | Episodio grave documentado (convulsiones, ingreso, glucagón). |

Este cálculo **no sustituye el juicio clínico**; es solo una ayuda para clasificar y priorizar la revisión de los registros.

### 7.5 Exportar Pacientes e Importar Pacientes

- **Exportar Pacientes**: descarga un archivo \`.json\` con **todos** los pacientes, medicamentos, registros de glucemia y registro de medicación.
- **Importar Pacientes**: carga un archivo \`.json\` previamente exportado. La app **valida el esquema** antes de cargarlo.

**Recomendación de frecuencia:** exporta **al menos una vez a la semana**.

**¿Dónde se guarda el archivo exportado?** En el **directorio de descargas por defecto** del dispositivo, que habitualmente es la carpeta **Descargas**.

---

## 8. Explicación detallada de cada sección

### 8.1 Cabecera y selector de paciente

La cabecera muestra el **nombre del paciente activo**, **edad y tipo de diabetes**, **unidad de glucosa** y **botones rápidos**: *Nuevo registro*, *Nueva dosis*, *Informe PDF*, *Enviar por correo*.

### 8.2 Panel de pacientes

Corresponde al array \`patients\`. Incluye \`id\`, \`name\`, \`dni\`, \`socialSecurity\`, \`gender\`, \`dateOfBirth\`, \`diabetesType\`, \`patientGroup\`, \`pregnancyStatus\`, \`pregnancyCategory\`, \`glucoseUnit\`, \`customTarget\`, \`medicines\`, \`medicationLog\`.

### 8.3 Panel de medicamentos

Corresponde al array \`medicines\`. Es importante que la **dosis predeterminada** y la **hora habitual** estén bien configuradas.

### 8.4 Registro de glucemias (records)

Cada registro tiene \`id\`, \`patientId\`, \`profile\`, \`date\`, \`meal\`, \`glucoseBefore\`, \`glucoseAfter\`, \`glucoseNight\`, \`exercise\`, \`comments\`, \`mood\`, \`moods\`, \`weather\`, \`example\`, \`severity\`, \`createdAt\`, \`dietContext\`.

### 8.5 Registro de medicación (medicationLog)

Cada entrada tiene \`id\`, \`medId\`, \`nombre\`, \`dosis\`, \`unidad\`, \`fecha\`, \`omitida\`, \`nota\`.

### 8.6 Meteorología

Campos: \`temp\`, \`humidity\`, \`precipitation\`, \`pressure\`, \`wind\`, \`date\`, \`location\`.

### 8.7 Ejercicio

Campos: \`type\` (walking, cycling, swimming, running, other), \`duration\` (minutos), \`steps\` (opcional).

### 8.8 Estado de ánimo

Valores: \`normal\`, \`estresado\`, \`ansioso\`, \`cansado\`, \`fatiga\`.

### 8.9 Contexto dietético

Valores: \`plan_recomendado\`, \`comida_familiar\`, \`exceso_cantidad\`, \`alcohol\`, \`salte_comida\`, \`comida_rapida\`, \`restaurante\`, \`evento_especial\`, \`comida_trabajo\`, \`otro_imprevisto\`.

### 8.10 Severidad

Se muestra como etiqueta de color: gris, verde, amarillo, naranja, rojo, rojo oscuro.

### 8.11 Panel de informes y PDF

Permite elegir rango de fechas, qué incluir, nivel de detalle, orientación, generar el PDF y enviar por correo (adjuntando el JSON).

> Recuerda: **las gráficas y la exportación a PDF necesitan conexión a internet**.

### 8.12 Exportar Pacientes / Importar Pacientes

- **Exportar Pacientes**: descarga un \`.json\` con todos los pacientes y registros.
- **Importar Pacientes**: carga un \`.json\`. Puedes elegir entre **fusionar** o **reemplazar**.
- **Validación**: la app comprueba el esquema antes de cargar.

---

## 9. Para profesionales sanitarios: datos de ejemplo (diabetes.json)

El archivo \`diabetes.json\` contiene **cinco pacientes de ejemplo** con **365 registros de glucemia** y **365 registros de medicación** cada uno, cubriendo un año completo (del **17 de septiembre de 2025** al **16 de septiembre de 2026**).

### 9.1 Cómo cargar los datos de ejemplo

Basta con pulsar **"Descargar datos de ejemplo"** en la pantalla inicial de la app. El archivo \`diabetes.json\` **se carga automáticamente**: la app lo lee directamente y **no es necesario buscarlo ni seleccionarlo manualmente** en el dispositivo.

### 9.2 Descripción de los cinco pacientes de ejemplo

#### 9.2.1 \`pt_es_sample_t1_01\` — Javier Manuel Ortega Díaz (Vigo)

- **Perfil**: varón, 41 años (nacido el 10/04/1985), diabetes tipo 1, adulto, no embarazado.
- **Medicamento**: Abasaglar (insulina glargina) 100 U/mL, vía subcutánea.
- **Pauta**: 12 UI a las 21:00.
  - **10/12/2025**: ajuste a **14 UI** tras revisión.
  - **24/12/2025**: ajuste a **16 UI**.
- **Utilidad**: caso **estable con ajuste progresivo de basal**.

#### 9.2.2 \`pt_es_dawn_phenomenon_02\` — Ana Maria Torres Gil (Barcelona)

- **Perfil**: mujer, 37 años (nacida el 03/11/1988), diabetes tipo 1, adulto, no embarazada.
- **Pauta**: 14 UI **a las 08:00**.
  - **24/12/2025**: cambio a **17 UI a las 20:30** (fenómeno del alba).
- **Utilidad**: caso de **fenómeno del alba**.

#### 9.2.3 \`pt_es_poor_adherence_02\` — Carlos Alberto Fernandez Lopez (Madrid)

- **Perfil**: varón, 44 años (nacido el 15/03/1982), diabetes tipo 1, adulto, no embarazado.
- **Pauta**: 16 UI a las 20:00.
  - **21/01/2026**: ajuste a **15 UI** (tras educación diabetológica).
- **Utilidad**: caso de **mala adherencia**.

#### 9.2.4 \`pt_es_hypo_dose_reduce_02\` — Laura Isabel Mendez Ruiz (Santiago de Compostela)

- **Perfil**: mujer, 35 años (nacida el 22/07/1990), diabetes tipo 1, adulto, no embarazada.
- **Pauta**: 18 UI a las 20:00.
  - **10/12/2025**: reducción a **14 UI** por hipoglucemias frecuentes.
- **Utilidad**: caso de **reducción de dosis por hipoglucemias**.

#### 9.2.5 \`pt_es_exercise_variability_02\` — Pablo Andres Molina Vega (Valencia)

- **Perfil**: varón, 33 años (nacido el 28/05/1993), diabetes tipo 1, adulto, no embarazado, sexo sin especificar.
- **Pauta**: 16 UI a las 20:00, con **ajustes puntuales a 14 UI los días de ejercicio intenso**.
- **Utilidad**: caso de **variabilidad por ejercicio**.

### 9.3 Opciones que conviene probar en los informes PDF

1. **Informe de 7 días** (\`pt_es_sample_t1_01\`, resumen ejecutivo).
2. **Informe de 30 días** (cualquiera, informe estándar).
3. **Informe de 90 días** (\`pt_es_dawn_phenomenon_02\`, informe completo).
4. **Informe de 365 días** (\`pt_es_hypo_dose_reduce_02\`, informe completo).
5. **Informe centrado en hipoglucemias** (\`pt_es_hypo_dose_reduce_02\`, 180 días).
6. **Informe centrado en adherencia** (\`pt_es_poor_adherence_02\`, 365 días).
7. **Informe centrado en ejercicio** (\`pt_es_exercise_variability_02\`, 90 días).
8. **Informe comparativo** (varios pacientes, 30 días, resumen).
9. **Informe con orientación horizontal** (cualquiera, 30 días, completo).
10. **Informe con rango personalizado** (\`pt_es_dawn_phenomenon_02\`, 10/12/2025–10/01/2026).

### 9.4 Guion de demostración sugerido

1. **Minuto 0–1**: abrir la app, mostrar la pantalla inicial con las dos opciones.
2. **Minuto 1–2**: pulsar **"Descargar datos de ejemplo"** (carga automática).
3. **Minuto 2–3**: mostrar el paciente activo y sus registros.
4. **Minuto 3–4**: generar un **informe de 30 días**.
5. **Minuto 4–5**: generar un **informe de 90 días** de \`pt_es_dawn_phenomenon_02\`.
6. **Minuto 5–6**: generar un **informe de 365 días** de \`pt_es_hypo_dose_reduce_02\`.
7. **Minuto 6–7**: usar **"Enviar por correo"**.
8. **Minuto 7–8**: mostrar **Exportar Pacientes** e **Importar Pacientes**.
9. **Minuto 8–9**: generar un **informe comparativo**.
10. **Minuto 9–10**: cerrar con la idea de flexibilidad y recordar el aviso legal.

---

## 10. Privacidad, seguridad y cumplimiento

- **Los datos no salen del dispositivo** salvo que tú decidas enviarlos por correo.
- **No hay cuentas ni contraseñas**.
- **Cifrado**: la app no cifra los datos. Usa el cifrado de disco del sistema operativo.
- **Recomendaciones**: exporta **semanalmente**, no compartas el \`.json\` por canales inseguros, revisa los campos antes de enviar, cumple con el RGPD y la LOPDGDD.

---

## 11. Preguntas frecuentes (FAQ)

**¿Necesito internet para usar la app?** Sí, para las gráficas, la exportación a PDF y la meteorología.

**¿Puedo usar la app en varios dispositivos?** Sí, pero no se sincronizan automáticamente.

**¿Qué pasa si borro los datos del navegador?** Se pierden. Exporta semanalmente.

**¿Puedo cambiar de mg/dL a mmol/L?** Sí, la app convierte automáticamente.

**¿Puedo tener varios pacientes?** Sí.

**¿Puedo registrar solo la insulina?** Sí.

**¿Puedo registrar una dosis omitida?** Sí, marca la casilla **"Omitida"**.

**¿Los informes PDF se envían a algún servidor?** No.

**¿Puedo usar la app en el móvil?** Sí.

**¿Qué hago si el PDF sale mal?** Revisa los márgenes de impresión.

**¿Cada cuánto debo exportar?** Al menos una vez a la semana.

**¿Dónde se guardan los archivos que descarga la app?** En el directorio de descargas por defecto (habitualmente la carpeta **Descargas**).

**¿Cada cuánto debo ir a la consulta?** La frecuencia la decide tu profesional sanitario. Orientación general: **cada 3 meses** (tipo 1 o tipo 2 insulinizada), **cada 6–12 meses** (tipo 2 no insulinizada o bien controlada).

**¿Qué hago si me falta un medicamento o una dosis está mal?** Contacta con tu clínica.

**¿Quién decide mi objetivo personalizado de glucemia?** Tu profesional sanitario.

**¿Se registra la categoría de embarazo (trimestre)?** No, la app no la registra.

---

## 12. Solución de problemas

| Problema | Causa probable | Solución |
|---|---|---|
| La app no carga | JavaScript desactivado o navegador antiguo | Activa JavaScript o actualiza el navegador |
| No se guardan los datos | Modo incógnito o almacenamiento lleno | Sal del modo incógnito o libera espacio |
| No aparecen las gráficas | Sin conexión a internet | Conéctate y recarga |
| No se genera el PDF | Sin conexión a internet | Conéctate y vuelve a intentarlo |
| No aparece la meteorología | Sin ubicación configurada o sin conexión | Configura la ubicación y comprueba la conexión |
| El PDF sale cortado | Márgenes de impresión | Ajusta los márgenes en el diálogo de impresión |
| La importación falla | Archivo corrupto o esquema incompatible | Comprueba el JSON |
| Las gráficas salen vacías | No hay datos en el rango seleccionado | Amplía el rango de fechas |
| Los valores se ven en otra unidad | Cambio de mg/dL a mmol/L | La app convierte automáticamente |
| No encuentro el JSON exportado | Se guarda en el directorio de descargas por defecto | Busca en la carpeta **Descargas** |

---

## 13. Glosario

- **Basal**: insulina de acción prolongada.
- **Bolo**: insulina de acción rápida antes de las comidas.
- **Fenómeno del alba**: hiperglucemia matutina.
- **HbA1c**: hemoglobina glicada.
- **Hipoglucemia**: glucemia por debajo de 70 mg/dL (3,9 mmol/L).
- **Hiperglucemia**: glucemia por encima de 180 mg/dL (10,0 mmol/L).
- **mg/dL**: miligramos por decilitro.
- **mmol/L**: milimoles por litro.
- **UI**: unidad internacional de insulina.
- **CIMA**: Centro de Información online de Medicamentos de la AEMPS.
- **NUSS**: Número de afiliación a la Seguridad Social. Formato español: 12 dígitos, habitualmente con barras y guiones: \`28/12345678-90\`.

---

## 14. Anexo A: esquema del archivo JSON

\`\`\`jsonc
{
  "patients": [
    {
      "id": "string",
      "name": "string",
      "dni": "string",
      "socialSecurity": "string",
      "gender": "male | female | unspecified",
      "dateOfBirth": "YYYY-MM-DD",
      "diabetesType": "type1 | type2 | gestational",
      "patientGroup": "adult | child_adolescent | pregnancy",
      "pregnancyStatus": "not_pregnant | pregnant | lactation | postpartum",
      "pregnancyCategory": "string",
      "glucoseUnit": "mgdl | mmoll",
      "customTarget": null,
      "medicines": [ /* ... */ ],
      "medicationLog": [ /* ... */ ]
    }
  ],
  "currentPatientId": "string",
  "records": [ /* ... */ ]
}
\`\`\`

---

## 15. Anexo B: valores admitidos en campos cerrados

**\`meal\`**: \`breakfast\`, \`lunch\`, \`dinner\`, \`snack\`, \`other\`.

**\`exercise.type\`**: \`walking\`, \`cycling\`, \`swimming\`, \`running\`, \`other\`.

**\`moods\`**: \`normal\`, \`estresado\`, \`ansioso\`, \`cansado\`, \`fatiga\`.

**\`dietContext\`**: \`plan_recomendado\`, \`comida_familiar\`, \`exceso_cantidad\`, \`alcohol\`, \`salte_comida\`, \`comida_rapida\`, \`restaurante\`, \`evento_especial\`, \`comida_trabajo\`, \`otro_imprevisto\`.

**\`severity\`**: \`null\`, \`mild\`, \`moderate\`, \`urgent\`, \`emergency\`, \`severe\`.

**\`gender\`**: \`male\`, \`female\`, \`unspecified\`.

**\`diabetesType\`**: \`type1\`, \`type2\`, \`gestational\`.

**\`patientGroup\`**: \`adult\`, \`child_adolescent\`, \`pregnancy\`.

**\`pregnancyStatus\`**: \`not_pregnant\`, \`pregnant\`, \`lactation\`, \`postpartum\`.

**\`glucoseUnit\`**: \`mgdl\`, \`mmoll\`.

---

*Fin del README. Recuerda: la app no diagnostica ni recomienda tratamientos; solo un profesional sanitario puede hacerlo. Consulta con tu equipo de diabetes la frecuencia de tus revisiones y contacta con tu clínica si necesitas corregir algún dato.*
