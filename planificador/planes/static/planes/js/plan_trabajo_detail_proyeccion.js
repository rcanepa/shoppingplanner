/*
Recibe la respuesta tipo AJAX que se genera al seleccionar un item a proyectar.
*/
function busquedaProyeccion(data){
    /* Se revisa que hayan ventas asociadas */
    if( data.ventas != null ){
        obj_trabajo.setProyeccion(data);
        crearTablaProyeccion(obj_trabajo.getProyeccion());
    }
    else{
        alert("El item seleccionado no es válido. Por favor verifique que haya escogido correctamente un item y que tenga los permisos necesarios para verlo");
    }
}

/*
Recibe la respuesta tipo AJAX que se genera al seleccionar un item a proyectar.
*/
function busquedaProyeccionComp(data){
    /* Se revisa que la busqueda haya devuelto ventas. */
    if( data.ventas != null ){
        $("#item-comparativo").text("Item: " + data.itemplan.nombre + " | " + numeral(data.itemplan.precio).format('0,0'));
        obj_trabajo.setProyeccionComp(data);
        crearTablaProyeccionComp(obj_trabajo.getProyeccionComp());
    }
    else{
        alert("El item seleccionado no es válido. Por favor verifique que haya escogido correctamente un item y que tenga los permisos necesarios para verlo");
    }
}

/*
Recibe como parametros datos de proyeccion y construye el HTML que genera una tabla de proyeccion
*/
function crearTablaProyeccion(data){
    var html_tot_vta_n = "";
    var html_tot_ctb_n = "";
    var html_tot_margen = "";
    var html_tot_unidades = "";
    var html = "";        
    html += "<table class=\"datagrid\" style=\"width:100%;\">";
    html += "<thead>";
    html += "<tr>";
    html += "<th style=\"width:16%;\">Temporada</th>";
    for (var x=0; x<data.periodos.length; x++){
        if (data.periodos[x].temporada){
            html += "<th title=\"Periodo de la temporada " 
                + data.temporada_vigente.nombre + " - " 
                + (parseInt(data.temporada_vigente.anio) - 1)  
                + "\" style=\"width:7%;background-color:#669;color:white\">" 
                + data.periodos[x].nombre + "</th>";
        }
        else
            html += "<th>" + data.periodos[x].nombre + "</th>";
    }
    html += "</tr>";
    html += "</thead>";
    html += "<tbody>";
    
    /* Se itera por cada temporada */
    $.each(data.ventas, function(temporada, ventas) {
        html += "<tr>";
        html += "<td class=\"separador\" colspan=\"13\"><b>Temporada: " + temporada + "</b></td>";
        html += "</tr>";

        /* Unidades vendidas */
        html += "<tr>";
        html += "<td title=\"Unidades vendidas.\" style=\"width:16%;\">Unidades</td>";
        $.each(ventas, function(periodo, venta) {
            if(venta.tipo != 0)
                html += "<td id=\"unidades_" + venta.periodo + "_" + temporada + "\" class=\"par unidades editable plan\">" + numeral(venta.vta_u).format('0,0') + "</td>";
            else
                html += "<td class=\"par unidades\">" + numeral(venta.vta_u).format('0,0') + "</td>";

        });
        html += "</tr>";
        
         /* Descuentos */
        html += "<tr>";
        html += "<td title=\"Descuento sobre el precio blanco.\" style=\"width:16%;\">Descuento %</td>";
        $.each(ventas, function(periodo, venta) {
            if(venta.tipo != 0)
                html += "<td id=\"descuentos_" + venta.periodo + "_" + temporada + "\" class=\"par descuentos editable plan\">" + numeral(venta.dcto).format('0.00%') + "</td>";
            else
                html += "<td class=\"par descuentos\">" + numeral(venta.dcto).format('0.00%') + "</td>";
        });
        html += "</tr>";

        /* Precio Real */
        html += "<tr>";
        html += "<td title=\"Precio real de venta.\" style=\"width:16%;\">Precio Real</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.precio_real).format('0,0') + "</td>";
        });
        html += "</tr>";

        /* Venta neta */
        html += "<tr>";
        html += "<td title=\"Venta en pesos.\" style=\"width:16%;\">Venta</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.vta_n).format('0,0') + "</td>";    
        });
        html += "</tr>";
        
         /* Contribucion */
        html += "<tr>";
        html += "<td title=\"Contribucion en pesos.\" style=\"width:16%;\">Contribuci&oacute;n</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.ctb_n).format('0,0') + "</td>";
        });
        html += "</tr>";
        
        /* Margen */
        html += "<tr>";
        html += "<td title=\"Margen porcentual.\" style=\"width:16%;\">Margen %</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.margen).format('0.00%') + "</td>";
        });
        html += "</tr>";

    });
    
    /* Totales */
    html += "<tr>";
    html += "<td class=\"separador\" colspan=\"13\"><b>Totales:</b></td>";
    html += "</tr>";
    for (var x=0; x<data.periodos.length; x++){
        var total_unidades = 0;
        var total_vta_n = 0;
        var total_ctb_n = 0;
        var total_margen = 0;
        $.each(data.ventas, function(temporada, ventas) {
            $.each(ventas, function(periodo, venta) {
                if (periodo == data.periodos[x].nombre){
                    total_unidades += parseFloat(venta.vta_u);
                    total_vta_n += parseFloat(venta.vta_n);
                    total_ctb_n += parseFloat(venta.ctb_n);
                    return false;
                }
            });

        });
        if (total_vta_n != 0)
            total_margen = total_ctb_n / total_vta_n;
        html_tot_unidades += "<td>" + numeral(total_unidades).format('0,0') + "</td>";
        html_tot_vta_n += "<td>" + numeral(total_vta_n).format('0,0') + "</td>";
        html_tot_ctb_n += "<td>" + numeral(total_ctb_n).format('0,0') + "</td>";
        html_tot_margen += "<td>" + numeral(total_margen).format('0.00%') + "</td>";
    }
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total unidades temporadas.\" style=\"width:16%;\">Unidades</td>";
    html += html_tot_unidades;
    html += "</tr>";
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total venta temporadas.\" style=\"width:16%;\">Venta</td>";
    html += html_tot_vta_n;
    html += "</tr>";
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total contribuci&oacute;n.\" style=\"width:16%;\">Contribuci&oacute;n</td>";
    html += html_tot_ctb_n;
    html += "</tr>";
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total margen.\" style=\"width:16%;\">Margen</td>";
    html += html_tot_margen;
    html += "</tr>";
    html += "</tbody>";
    html += "</table>";
    $("#tab_proyeccion").html(html);
    $(".editable").click(proyectarCelda);
}

/*
Recibe como parametros datos de proyeccion y construye el HTML que genera una tabla de proyeccion.
La informacion de esta tabla no es editable.
*/
function crearTablaProyeccionComp(data){

    var html_tot_vta_n = "";
    var html_tot_ctb_n = "";
    var html_tot_margen = "";
    var html_tot_unidades = "";
    var html = "";        
    html += "<table class=\"datagrid\" style=\"width:100%;\">";
    html += "<thead>";
    html += "<tr>";
    html += "<th style=\"width:16%;\">Temporada</th>";
    for (var x=0; x<data.periodos.length; x++){
        if (data.periodos[x].temporada){
            html += "<th title=\"Periodo de la temporada " 
                + data.temporada_vigente.nombre + " - " 
                + (parseInt(data.temporada_vigente.anio) - 1)  
                + "\" style=\"width:7%;background-color:#669;color:white\">" 
                + data.periodos[x].nombre + "</th>";
        }
        else
            html += "<th style=\"width:7%;\">" + data.periodos[x].nombre + "</th>";
    }
    html += "</tr>";
    html += "</thead>";
    html += "<tbody>";
    
    /* Se itera por cada temporada */
    $.each(data.ventas, function(temporada, ventas) {

        html += "<tr>";
        html += "<td class=\"separador\" colspan=\"13\"><b>Temporada: " + temporada + "</b></td>";
        html += "</tr>";

        /* Unidades vendidas */
        html += "<tr>";
        html += "<td title=\"Unidades vendidas.\" style=\"width:16%;\">Unidades</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par unidades\">" + numeral(venta.vta_u).format('0,0') + "</td>";
        });
        html += "</tr>";
        
         /* Descuentos */
        html += "<tr>";
        html += "<td title=\"Descuento sobre el precio blanco.\" style=\"width:16%;\">Descuento %</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par descuentos\">" + numeral(venta.dcto).format('0.00%') + "</td>";
        });
        html += "</tr>";

        /* Precio Real */
        html += "<tr>";
        html += "<td title=\"Precio real de venta.\" style=\"width:16%;\">Precio Real</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.precio_real).format('0,0') + "</td>";
        });
        html += "</tr>";

        /* Venta neta */
        html += "<tr>";
        html += "<td title=\"Venta en pesos.\" style=\"width:16%;\">Venta</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.vta_n).format('0,0') + "</td>";
        });
        html += "</tr>";
        
         /* Contribucion */
        html += "<tr>";
        html += "<td title=\"Contribucion en pesos.\" style=\"width:16%;\">Contribuci&oacute;n</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.ctb_n).format('0,0') + "</td>";
        });
        html += "</tr>";
        
        /* Margen */
        html += "<tr>";
        html += "<td title=\"Margen porcentual.\" style=\"width:16%;\">Margen %</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.margen).format('0.00%') + "</td>";
        });
        html += "</tr>";

    });
    
    /* Totales */
    html += "<tr>";
    html += "<td class=\"separador\" colspan=\"13\"><b>Totales:</b></td>";
    html += "</tr>";
    for (var x=0; x<data.periodos.length; x++){
        var total_unidades = 0;
        var total_vta_n = 0;
        var total_ctb_n = 0;
        var total_margen = 0;
        $.each(data.ventas, function(temporada, ventas) {
            $.each(ventas, function(periodo, venta) {
                if (periodo == data.periodos[x].nombre){
                    total_unidades += parseFloat(venta.vta_u);
                    total_vta_n += parseFloat(venta.vta_n);
                    total_ctb_n += parseFloat(venta.ctb_n);
                    return false;
                }
            });
        });
        if (total_vta_n != 0)
            total_margen = total_ctb_n / total_vta_n;
        html_tot_unidades += "<td>" + numeral(total_unidades).format('0,0') + "</td>";
        html_tot_vta_n += "<td>" + numeral(total_vta_n).format('0,0') + "</td>";
        html_tot_ctb_n += "<td>" + numeral(total_ctb_n).format('0,0') + "</td>";
        html_tot_margen += "<td>" + numeral(total_margen).format('0.00%') + "</td>";
    }
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total unidades temporadas.\" style=\"width:16%;\">Unidades</td>";
    html += html_tot_unidades;
    html += "</tr>";
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total venta temporadas.\" style=\"width:16%;\">Venta</td>";
    html += html_tot_vta_n;
    html += "</tr>";
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total contribuci&oacute;n.\" style=\"width:16%;\">Contribuci&oacute;n</td>";
    html += html_tot_ctb_n;
    html += "</tr>";
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total margen.\" style=\"width:16%;\">Margen</td>";
    html += html_tot_margen;
    html += "</tr>";
    html += "</tbody>";
    html += "</table>";
    $("#tab_comparativo").html(html);
}

/*
Despliega un dialog cada vez que un usuario hace click sobre una celda editable
de una tabla de proyeccion.
*/
function proyectarCelda(){
    // Se asigna a td la celda que ha sido presionada para proyectar su valor
    obj_trabajo.setCeldaEditada($(this));
    // Se hace un split sobre el id de la celda para obtener el tipo de celda (unidad o dcto), periodo y temporada
    parametros = obj_trabajo.getCeldaEditada().attr("id").split("_");
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
Actualiza el atributo proyeccion del objeto obj_trabajo segun las
modificaciones que haya hecho el usuario en la tabla de proyeccion.
*/
function actualizarProyeccion(metrica, periodo, temporada){
        proyeccion = obj_trabajo.getProyeccion();
        // Si se proyectaron las unidades, se entra al ciclo if
        if(metrica == 'unidades'){
            $.each(proyeccion.ventas[temporada], function(periodo_venta, venta) {
                if(periodo_venta == periodo.trim()){
                    // Se asigna tipo temporal 3 (proyectada no guardada)
                    venta.tipo = 3;
                    // Se lee el valor de la celda y se quita su formato
                    venta.vta_u = numeral().unformat(obj_trabajo.getCeldaEditada().text());

                    // Venta Neta
                    venta.vta_n = parseFloat( (1 - venta.dcto) * venta.vta_u * proyeccion.itemplan.precio / 1.19 );
                    
                    // Contribucion
                    venta.ctb_n = parseFloat(venta.vta_n - (venta.vta_u * proyeccion['itemplan'].costo_unitario)).toFixed(1);
                    
                    // Margen                   
                    if(venta.vta_n != 0)
                        venta.margen = venta.ctb_n / venta.vta_n;

                    // Precio Real
                    if(venta.vta_n != 0)
                        venta.precio_real = venta.vta_n / venta.vta_u * 1.19;

                    // Costo
                    venta.costo = parseFloat(venta.vta_u * proyeccion['itemplan'].costo_unitario).toFixed(1);

                    crearTablaProyeccion(proyeccion);
                }
            });
        }
        // Si se proyectaron los descuentos, se entra al ciclo if
        else if(metrica == 'descuentos'){
            $.each(proyeccion.ventas[temporada], function(periodo_venta, venta) {
                if(periodo_venta == periodo.trim()){
                    // Se asigna tipo temporal 3 (proyectada no guardada)
                    venta.tipo = 3;
                    // Se lee el valor de la celda y se quita su formato
                    venta.dcto = numeral().unformat(obj_trabajo.getCeldaEditada().text());
                    
                    // Venta Neta
                    venta.vta_n = parseFloat( (1 - venta.dcto) * venta.vta_u * proyeccion.itemplan.precio / 1.19 );
                    
                    // Contribucion
                    venta.ctb_n = parseFloat(venta.vta_n - (venta.vta_u * proyeccion['itemplan'].costo_unitario)).toFixed(1);
                    
                    // Margen                   
                    if(venta.vta_n != 0)
                        venta.margen = venta.ctb_n / venta.vta_n;

                    // Precio Real
                    if(venta.vta_n != 0)
                        venta.precio_real = venta.vta_n / venta.vta_u * 1.19;

                    crearTablaProyeccion(proyeccion);
                }
            });
        }
        obj_trabajo.setProyeccion(proyeccion);
    }