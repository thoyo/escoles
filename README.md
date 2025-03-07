# TODO
* load postgres creds from env
* add in item details (map and list)
    * forecast of remaining spots this year
    * ~~remaining spots last year~~
    * ~~total spots~~
* allow sorting by the previous fields
* make the timeseries rounded
* add label with school name on the map always
* add timeseries about
    * offers
    * remaining spots after first round
    * ~~remaining spots~~
* add other info about surrounding
    * distance to park
    * pollution
    * noise level
* unittest that asserts equal results as in https://www.edubcn.cat/ca/alumnat_i_familia/informacio_general_matriculacio/arees_influencia/consulta_de_centres_educatius#/centres/... 

* ~~display the 500m radius~~
* ~~color code public and concertated schools~~
* ~~display the areas~~
* ~~add choice selector that allows to choose between~~
  * ~~showing centers for which max points will be obtained~~
  * ~~showing centers at less than given distance (and add slider to select dist, from 0 to inf). And add privates in this case~~
* ~~remove non barcelonian areas and warn about clicking outside barcelona~~
* ~~remove private centers~~
* ~~add email and website of the center~~
* ~~hyperlink with link to google maps the address to the center~~
* ~~lint the frontend~~
* ~~add placemark for home~~
* ~~show "list" view alongside the map~~
* ~~add also checking for at least 6 centers of each type~~
* ~~log activity to postgres~~
* ~~setup grafana for observability~~
* ~~dont make the url with trailing slash fail~~

# refs
  * https://educacio.gencat.cat/web/.content/home/arees-actuacio/centres-serveis-educatius/centres/directori-centres/codisnivellseducatius.pdf
  * https://www.edubcn.cat/rcs_gene/extra/02_proximitat/BCN_211004_OBLIGATORIS_MAPA_2021-2022.pdf
  * https://www.edubcn.cat/ca/alumnat_i_familia/informacio_general_matriculacio/arees_influencia/que_son
  * https://opendata-ajuntament.barcelona.cat/data/es/dataset/20170706-districtes-barris/resource/5f8974a7-7937-4b50-acbc-89204d570df9
  * http://mapaescolar.gencat.cat/index.html
  * https://analisi.transparenciacatalunya.cat/Educaci-/Directori-de-centres-docents-TRA-ACOVID/3u9c-b74b/data_preview
    * Missing centers (e.g says that "Cargol" is only for adults)
    * Wrong coords (e.g for Coves d'en Cimany, puts it in Calafell instead of in Barcelona)
  * https://analisi.transparenciacatalunya.cat/Educaci-/Directori-de-centres-docents-anual-Base-2020/kvmv-ahh4/about_data
    * Wrong coords (e.g for Sadako)
  * http://mapaescolar.gencat.cat/
    * Exported xls contains a CSV that differentiates between concertated and private schools
    * Getting good coordinates for all
  * https://analisi.transparenciacatalunya.cat/Educaci-/Estad-stica-de-l-assignaci-de-places-en-el-proc-s-/99md-r3rq/about_data


# [assignations_data](assignations_data)
Data extracted from https://glorialangreo.com/schools/

