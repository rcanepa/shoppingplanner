/*
Recibe la respuesta tipo AJAX que se genera al seleccionar un item a proyectar.
*/
function busquedaProyeccion(data){
    /* Se revisa que hayan ventas asociadas */
    if( data.ventas != null ){
        obj_trabajo.setDatos(data);
        crearTablaProyeccion(obj_trabajo.getDatos());
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
        $("#item_proyeccion_comp").text("Item: " + data.itemplan.nombre + " | " + numeral(data.itemplan.precio).format('0,0'));
        obj_trabajo.setDatosComp(data);
        crearTablaProyeccionComp(obj_trabajo.getDatosComp());
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
    var anio_th = 0;
    var colspan_anio_th = 0;
    html += "<table class=\"datagrid\" style=\"width:100%;\">";
    html += "<thead>";
    /* Aqui se genera la cabecera TH con los años */
    html += "<tr>";
    html += "<th></th>";
    anio_th = data.periodos[0].tiempo__anio;
    for (var x=0; x<data.periodos.length; x++){
        if ( data.periodos[x].tiempo__anio != anio_th){
            html += "<th colspan=\"" + colspan_anio_th + "\">" + anio_th + "</th>";
            colspan_anio_th = 0;
            anio_th = data.periodos[x].tiempo__anio;
        }
        colspan_anio_th++;
    }
    html += "<th colspan=\"" + colspan_anio_th + "\">" + anio_th + "</th>";
    html += "</tr>";
    html += "<tr>";
    html += "<th>Temporada</th>";
    for (var x=0; x<data.periodos.length; x++){
        if (data.periodos[x].temporada){
            html += "<th title=\"Periodo de la temporada " 
                + data.temporada_vigente.nombre + " - " 
                + (parseInt(data.temporada_vigente.anio) - 1)  
                + "\" style=\"background-color:#F5F5ED;\">" 
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
        html += "<td title=\"Unidades vendidas.\">Unidades</td>";
        $.each(ventas, function(periodo, venta) {
            if(venta.tipo != 0)
                html += "<td id=\"unidades_" + venta.periodo + "_" + temporada + "\" class=\"par unidades editable plan\">" + numeral(venta.vta_u).format('0,0') + "</td>";
            else
                html += "<td class=\"par unidades\">" + numeral(venta.vta_u).format('0,0') + "</td>";

        });
        html += "</tr>";
        
         /* Descuentos */
        html += "<tr>";
        html += "<td title=\"Descuento sobre el precio blanco.\">Descuento %</td>";
        $.each(ventas, function(periodo, venta) {
            if(venta.tipo != 0)
                html += "<td id=\"descuentos_" + venta.periodo + "_" + temporada + "\" class=\"par descuentos editable plan\">" + numeral(venta.dcto).format('0.00%') + "</td>";
            else
                html += "<td class=\"par descuentos\">" + numeral(venta.dcto).format('0.00%') + "</td>";
        });
        html += "</tr>";

        /* Precio Real */
        html += "<tr>";
        html += "<td title=\"Precio real de venta.\">Precio Real</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.precio_real).format('0,0') + "</td>";
        });
        html += "</tr>";

        /* Venta neta */
        html += "<tr>";
        html += "<td title=\"Venta en pesos.\">Venta</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.vta_n).format('0,0') + "</td>";    
        });
        html += "</tr>";
        
         /* Contribucion */
        html += "<tr>";
        html += "<td title=\"Contribucion en pesos.\">Contribuci&oacute;n</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.ctb_n).format('0,0') + "</td>";
        });
        html += "</tr>";
        
        /* Margen */
        html += "<tr>";
        html += "<td title=\"Margen porcentual.\">Margen %</td>";
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
    html += "<td title=\"Total unidades temporadas.\">Unidades</td>";
    html += html_tot_unidades;
    html += "</tr>";
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total venta temporadas.\">Venta</td>";
    html += html_tot_vta_n;
    html += "</tr>";
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total contribuci&oacute;n.\">Contribuci&oacute;n</td>";
    html += html_tot_ctb_n;
    html += "</tr>";
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total margen.\">Margen</td>";
    html += html_tot_margen;
    html += "</tr>";
    html += "</tbody>";
    html += "</table>";
    $("#tab_proyeccion").html(html);
    $(".editable").click(modificarCelda);
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
    var anio_th = 0;
    var colspan_anio_th = 0;
    html += "<table class=\"datagrid\" style=\"width:100%;\">";
    html += "<thead>";
    /* Aqui se genera la cabecera TH con los años */
    html += "<tr>";
    html += "<th></th>";
    anio_th = data.periodos[0].tiempo__anio;
    for (var x=0; x<data.periodos.length; x++){
        if ( data.periodos[x].tiempo__anio != anio_th){
            html += "<th colspan=\"" + colspan_anio_th + "\">" + anio_th + "</th>";
            colspan_anio_th = 0;
            anio_th = data.periodos[x].tiempo__anio;
        }
        colspan_anio_th++;
    }
    html += "<th colspan=\"" + colspan_anio_th + "\">" + anio_th + "</th>";
    html += "</tr>";
    html += "<tr>";
    html += "<th>Temporada</th>";
    for (var x=0; x<data.periodos.length; x++){
        if (data.periodos[x].temporada){
            html += "<th title=\"Periodo de la temporada " 
                + data.temporada_vigente.nombre + " - " 
                + (parseInt(data.temporada_vigente.anio) - 1)  
                + "\" style=\"background-color:#F5F5ED;\">" 
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
        html += "<td title=\"Unidades vendidas.\">Unidades</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par unidades\">" + numeral(venta.vta_u).format('0,0') + "</td>";
        });
        html += "</tr>";
        
         /* Descuentos */
        html += "<tr>";
        html += "<td title=\"Descuento sobre el precio blanco.\">Descuento %</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par descuentos\">" + numeral(venta.dcto).format('0.00%') + "</td>";
        });
        html += "</tr>";

        /* Precio Real */
        html += "<tr>";
        html += "<td title=\"Precio real de venta.\">Precio Real</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.precio_real).format('0,0') + "</td>";
        });
        html += "</tr>";

        /* Venta neta */
        html += "<tr>";
        html += "<td title=\"Venta en pesos.\">Venta</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.vta_n).format('0,0') + "</td>";
        });
        html += "</tr>";
        
         /* Contribucion */
        html += "<tr>";
        html += "<td title=\"Contribucion en pesos.\">Contribuci&oacute;n</td>";
        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.ctb_n).format('0,0') + "</td>";
        });
        html += "</tr>";
        
        /* Margen */
        html += "<tr>";
        html += "<td title=\"Margen porcentual.\">Margen %</td>";
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
    html += "<td title=\"Total unidades temporadas.\">Unidades</td>";
    html += html_tot_unidades;
    html += "</tr>";
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total venta temporadas.\">Venta</td>";
    html += html_tot_vta_n;
    html += "</tr>";
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total contribuci&oacute;n.\">Contribuci&oacute;n</td>";
    html += html_tot_ctb_n;
    html += "</tr>";
    html += "<tr class=\"par totales\">";
    html += "<td title=\"Total margen.\">Margen</td>";
    html += html_tot_margen;
    html += "</tr>";
    html += "</tbody>";
    html += "</table>";
    $("#tab_comparativo").html(html);
}

/*
Actualiza el atributo datos del objeto obj_trabajo segun las
modificaciones que haya hecho el usuario en la tabla de proyeccion/planificacionAS.
*/
function actualizarProyeccion(metrica, periodo, temporada){
    proyeccion = obj_trabajo.getDatos();
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
    obj_trabajo.setDatos(proyeccion);
}