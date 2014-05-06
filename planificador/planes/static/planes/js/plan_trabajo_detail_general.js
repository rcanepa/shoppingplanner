/*
    Controla los cambios hechos sobre el combobox de itemplan.
    Gatilla una busqueda sobre la informacion comercial del itemplan
    seleccionado.
*/
function busquedaAJAXdatos(){
    /* Se determina el tipo de tarea que esta realizando el usuario para
    buscar la informacion necesaria (proyeccion, planificacion o resumen) */
    obj_trabajo.setItem($(this).val());
    desactivarGuardar();
    obj_trabajo.setModificada(false);
    if (obj_trabajo.getItem() != -1){
        switch(obj_trabajo.getActividad()){
            case 1:
                data = {'id_itemplan':obj_trabajo.getItem(), 'id_plan':obj_trabajo.getPlan()};
                url = '/planes/plan/buscar-datos-proyeccion/';
                busqueda = busquedaProyeccion;
                break;
            case 2:
                data = {'id_itemplan':obj_trabajo.getItem(), 'id_plan':obj_trabajo.getPlan()};
                url = '/planes/plan/buscar-datos-planificacion-tv/';
                busqueda = busquedaPlanificacionTV;
                break;
            case 3:
                data = {'id_itemplan':obj_trabajo.getItem(), 'id_plan':obj_trabajo.getPlan()};
                url = '/planes/plan/buscar-datos-planificacion-as/';
                busqueda = busquedaPlanificacionAS;
                break;
            case 4:
                data = {'id_item':obj_trabajo.getItem(), 'id_plan':obj_trabajo.getPlan(), 'id_temporada':0, 'tipo_obj_item':'itemplan'};
                url = '/planes/plan/buscar-datos-resumen/';
                busqueda = busquedaResumen;
                break;
        }
        
        var request = $.ajax({
            data: data,
            url: url,
            type: 'get'
        });

        request.done(busqueda);
    }        
}

/*
    Controla los cambios hechos sobre el combobox de itemplan de comparacion.
    Gatilla una busqueda sobre la informacion comercial del itemplan
    seleccionado.
*/
function busquedaAJAXdatosComp(id_item){
    /* Se determina el tipo de tarea que esta realizando el usuario para
    buscar la informacion necesaria (proyeccion, planificacion o resumen) */
    obj_trabajo.setItemComp(id_item);
    switch(obj_trabajo.getActividad()){
        case 1:
            data = {'id_item':id_item, 'id_plan':obj_trabajo.getPlan()};
            url = '/planes/plan/buscar-datos-proyeccion-comp/';
            busqueda = busquedaProyeccionComp;
            break;
        case 2:
            data = {'id_item':id_item, 'id_plan':obj_trabajo.getPlan()};
            url = '/planes/plan/buscar-datos-planificacion-tv-comp/';
            busqueda = busquedaPlanificacionTVComp;
            break;
        case 3:
            data = {'id_item':id_item, 'id_plan':obj_trabajo.getPlan()};
            url = '/planes/plan/buscar-datos-planificacion-as-comp/';
            busqueda = busquedaPlanificacionASComp;
            break;
        case 4:
            data = {'id_item':id_item, 'id_plan':obj_trabajo.getPlan(), 'id_temporada':0, 'tipo_obj_item':'item'};
            url = '/planes/plan/buscar-datos-resumen/';
            busqueda = busquedaResumenComp;
            break;
    }

    var request = $.ajax({
        data: data,
        url: url,
        type: 'get'
    });

    request.done(busqueda);
}

/*
Se preocupa de cargar los elementos SELECT para la seleccion del item a trabajar.
*/
function buscarCategoria(){
    var id_this = $(this).attr("id");
    var id_item = $(this).val();
    var id_plan = obj_trabajo.getPlan();
    if(id_item != -1){
        $.ajax({
            data: {'id_item':id_item, 'id_plan':id_plan},
            url: '/planes/plan/buscar-lista-items/',
            type: 'get',
            success: function(data){
                desactivarGuardar();
                obj_trabajo.setModificada(false);
                limpiarHTML(0);
                obj_trabajo.limpiarItem();
                html = '';
                html += "<option value=\"-1\"></option>"
                for (var x=0; x<data.items.length; x++){
                    // Se revisa si el tipo de resultado es una lista de itemplan (combo de resultado) o items (combo de busqueda o comparacion)
                    if ( typeof data.items[x].precio === "undefined" )
                            html += '<option value="' + data.items[x].id + '">' + data.items[x].nombre + '</option>';
                    else
                        html += '<option value="' 
                        + data.items[x].id + '">' 
                        + data.items[x].estado + ' | ' 
                        //+ data.items[x].categoria_nombre + ' | ' 
                        + data.items[x].nombre + ' | ' 
                        + numeral(data.items[x].precio).format('0,0') + '</option>';
                }
                // Se revisa si la categoria es planificable (por lo tanto carga el resultado en el combo de items)
                if (!data.categoria.planificable)
                    $("#combo_cat_proy_" + data.categoria.id_categoria).html(html);
                else
                    $("#combo_resultado").html(html);       
            }
        });
    }
    else{
    }
}

/*
Se preocupa de cargar los elementos SELECT para la seleccion del item a comparar.
*/
function buscarCategoriaComparacion(){
    var id_this = $(this).attr("id");
    var id_this_arry = id_this.split("_");
    var id_item = $("#combo_cat_comp_" + id_this_arry[3]).val();
    var id_plan = obj_trabajo.getPlan();
    if(id_item != -1){
        $.ajax({
            data: {'id_item':id_item, 'id_plan':id_plan},
            url: '/planes/plan/buscar-lista-items-comparacion/',
            type: 'get',
            success: function(data){
                limpiarHTML(1);
                obj_trabajo.limpiarItemComparativo();
                if ( data.items != null ){
                    html = '';
                    html += "<option value=\"-1\"></option>"
                    for (var x=0; x<data.items.length; x++){
                        if ( data.items[x].precio != 0 )
                            html += '<option value="' + data.items[x].id + '">' + data.items[x].nombre + ' | ' + numeral(data.items[x].precio).format('0,0') + '</option>';
                        else
                            html += '<option value="' + data.items[x].id + '">' + data.items[x].nombre + '</option>';
                    }
                    $("#combo_cat_comp_" + data.categoria.id_categoria).html(html);
                }
                else{
                }
            }
        });
    }
}

/*
Despliega un dialog cada vez que un usuario hace click sobre una celda editable
de una tabla de proyeccion/planificacionAS.
*/
function modificarCelda(){
    // Se asigna a td la celda que ha sido presionada para proyectar su valor
    obj_trabajo.setCeldaEditada($(this));
    // Se hace un split sobre el id de la celda para obtener el tipo de celda (unidad o dcto), periodo y temporada
    var parametros = obj_trabajo.getCeldaEditada().attr("id").split("_");
    // Se agrega el valor de la celda al input box del dialog
    $("#inputval").val(obj_trabajo.getCeldaEditada().text());
    // Se customiza el mensaje del dialog en base al tipo de celda que se esta proyectando
    if(parametros[0] == 'unidades')
        $("#dialog_help_msg").text("Ingresar unidades:");
    else
        $("#dialog_help_msg").text("Ingresar porcentaje (0%-100%):");
    $( "#dialog-box" ).dialog( "open" );
    $( "#dialog-box input[type=text]" ).select();
}

/*
Se encarga de borrar el contenido de los DIVS de proyeccion y planificacion. Tambien
elimina los datos de los comparativos.
*/
function limpiarHTML(tipo){
    switch(tipo){
        case 0:  /* Cambio en el combobox de trabajo */
            $( ".tabla_datos_actividad" ).html("");
            break;
        case 1:  /* Cambio en el combobox de comparativo */
            $( ".tabla_datos_actividad_comp" ).html("");
            break;
    }
}

/*
Deshabilita el boton de guardar modificaciones.
*/
function desactivarGuardar(){
    if ( !$("#panel-acciones").hasClass("pure-menu-disabled") )
        $("#panel-acciones").addClass("pure-menu-disabled");
}

/*
Habilita el boton de guardar modificaciones.
*/
function activarGuardar(){
    if ( $("#panel-acciones").hasClass("pure-menu-disabled") )
        $("#panel-acciones").removeClass("pure-menu-disabled");
}

/*
Devuelve true o false dependiendo de si el boton
se encuentra activado o desactivado.
*/
function verificarGuardar(){
    return !$("#panel-acciones").hasClass("pure-menu-disabled");
}