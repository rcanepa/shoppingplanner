/*
Recibe la respuesta tipo AJAX que se genera al seleccionar un item a planificar.
*/
function busquedaPlanificacionAS(data){
    // Se revisa que la busqueda haya devuelto ventas. Si no devolvio datos de venta significa que no encontro el item
    // que se estaba buscando
    if( data.ventas != null ){
        obj_trabajo.setDatos(data);
        crearTablaPlanificacionAS(data);
    }
    else{
        alert("El item seleccionado no es válido. Por favor verifique que haya escogido correctamente un item y que tenga los permisos necesarios para verlo");
    }
}

/*
Recibe la respuesta tipo AJAX que se genera al seleccionar un item a proyectar.
*/
function busquedaPlanificacionASComp(data){
    if( data.ventas != null ){
        $("#nombre_item_comp").text("Item: " + data.itemplan.nombre + " | " + numeral(data.itemplan.precio).format('0,0'));
        obj_trabajo.setDatosComp(data);
        crearTablaPlanificacionASComp(data);
    }
    else{
        alert("El item seleccionado no es válido. Por favor verifique que haya escogido correctamente un item y que tenga los permisos necesarios para verlo");
    }
}

function crearTablaPlanificacionAS(data){

    var html_tot_vta_n = "";
    var html_tot_ctb_n = "";
    var html_tot_margen = "";
    var html_tot_unidades = "";
    var html = "";
    var html_div_etiquetas = "";
    var anio_th = 0;
    var colspan_anio_th = 0;
    html += "<table class=\"datagrid\" style=\"width:100%;\">";
    html += "<thead>";
    html_div_etiquetas += "<table class=\"datagrid\">";
    html_div_etiquetas += "<thead>";
    html_div_etiquetas += "<tr>";
    html_div_etiquetas += "<th class=\"label\">Año</th>";
    /* Aqui se genera la cabecera TH con los años */
    html += "<tr>";
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
    html_div_etiquetas += "</tr>";
    html_div_etiquetas += "<tr>";
    html_div_etiquetas += "<th class=\"label\">Periodo</th>";
    html += "<tr>";
    for (var x=0; x<data.periodos.length; x++){
        if (data.periodos[x].temporada){
            html += "<th title=\"Periodo de la temporada " 
                + data.temporada_vigente.nombre + " - " 
                + (parseInt(data.temporada_vigente.anio))  
                + "\" style=\"background-color:#F5F5ED;\">" 
                + data.periodos[x].nombre + "</th>";
        }
        else
            html += "<th>" + data.periodos[x].nombre + "</th>";
    }
    html += "</tr>";
    html += "</thead>";
    html += "<tbody>";
    html_div_etiquetas += "</tr>";
    html_div_etiquetas += "</thead>";
    html_div_etiquetas += "<tbody>";
    
    /* Se itera por cada temporada */
    $.each(data.ventas, function(temporada, ventas) {
        html += "<tr>";
        html += "<td class=\"separador\" colspan=\"12\">-</td>";
        html += "</tr>";

        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td class=\"separador\"><b>Temporada: " + temporada + "</b></td>";
        html_div_etiquetas += "</tr>";

        /* Unidades vendidas */
        html += "<tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td title=\"Unidades vendidas.\" class=\"label\">Unidades</td>";

        $.each(ventas, function(periodo, venta) {
            if(venta.tipo != 0)
                html += "<td id=\"unidades_" + venta.periodo + "_" + temporada + "\" class=\"par unidades editable plan\">" + numeral(venta.vta_u).format('0,0') + "</td>";
            else
                html += "<td class=\"par unidades\">" + numeral(venta.vta_u).format('0,0') + "</td>";

        });
        html += "</tr>";
        html_div_etiquetas += "</tr>";
        
         /* Descuentos */
        html += "<tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td title=\"Descuento sobre el precio blanco.\" class=\"label\">Dcto. %</td>";

        $.each(ventas, function(periodo, venta) {
            if(venta.tipo != 0)
                html += "<td id=\"descuentos_" + venta.periodo + "_" + temporada + "\" class=\"par descuentos editable plan\">" + numeral(venta.dcto).format('0.00%') + "</td>";
            else
                html += "<td class=\"par descuentos\">" + numeral(venta.dcto).format('0.00%') + "</td>";
        });
        html += "</tr>";
        html_div_etiquetas += "</tr>";

        /* Precio Real */
        html += "<tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td title=\"Precio real de venta.\" class=\"label\">Precio Real</td>";

        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.precio_real).format('0,0') + "</td>";
        });
        html += "</tr>";
        html_div_etiquetas += "</tr>";

        /* Venta neta */
        html += "<tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td title=\"Venta en pesos.\" class=\"label\">Venta</td>";

        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.vta_n).format('0,0') + "</td>";    
        });
        html += "</tr>";
        html_div_etiquetas += "</tr>";
        
         /* Contribucion */
        html += "<tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td title=\"Contribucion en pesos.\" class=\"label\">Contribuci&oacute;n</td>";

        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.ctb_n).format('0,0') + "</td>";
        });
        html += "</tr>";
        html_div_etiquetas += "</tr>";
        
        /* Margen */
        html += "<tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td title=\"Margen porcentual.\" class=\"label\">Margen %</td>";

        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.margen).format('0.00%') + "</td>";
        });
        html += "</tr>";
        html_div_etiquetas += "</tr>";

    });
    
    /* Totales */
    html += "<tr>";
    html += "<td class=\"separador\" colspan=\"12\">-</td>";
    html += "</tr>";
    html_div_etiquetas += "<tr>";
    html_div_etiquetas += "<td class=\"separador\"><b>Totales:</b></td>";
    html_div_etiquetas += "</tr>";
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
            total_margen = (total_ctb_n / total_vta_n).toFixed(3);
        html_tot_unidades += "<td>" + numeral(total_unidades).format('0,0') + "</td>";
        html_tot_vta_n += "<td>" + numeral(total_vta_n).format('0,0') + "</td>";
        html_tot_ctb_n += "<td>" + numeral(total_ctb_n).format('0,0') + "</td>";
        html_tot_margen += "<td>" + numeral(total_margen).format('0.00%') + "</td>";
    }
    html += "<tr class=\"par totales\">";
    html += html_tot_unidades;
    html += "</tr>";
    html_div_etiquetas += "<tr class=\"totales\">";
    html_div_etiquetas += "<td title=\"Total unidades temporadas.\" class=\"label\">Unidades</td>";
    html_div_etiquetas += "</tr>";

    html += "<tr class=\"par totales\">";
    html += html_tot_vta_n;
    html += "</tr>";
    html_div_etiquetas += "<tr class=\"totales\">";
    html_div_etiquetas += "<td title=\"Total venta temporadas.\" class=\"label\">Venta</td>";
    html_div_etiquetas += "</tr>";

    html += "<tr class=\"par totales\">";
    html += html_tot_ctb_n;
    html += "</tr>";
    html_div_etiquetas += "<tr class=\"totales\">";
    html_div_etiquetas += "<td title=\"Total contribuci&oacute;n.\" class=\"label\">Contribuci&oacute;n</td>";
    html_div_etiquetas += "</tr>";

    html += "<tr class=\"par totales\">";
    html += html_tot_margen;
    html += "</tr>";
    html_div_etiquetas += "<tr class=\"totales\">";
    html_div_etiquetas += "<td title=\"Total margen.\" class=\"label\">Margen</td>";
    html_div_etiquetas += "</tr>";
    
    html += "</tbody>";
    html += "</table>";
    html_div_etiquetas += "</tbody>";
    html_div_etiquetas += "</table>";

    $("#div_etiquetas").html(html_div_etiquetas);
    $("#div_datos").html(html);
    $(".editable").click(modificarCelda);
}

function crearTablaPlanificacionASComp(data){

    var html_tot_vta_n = "";
    var html_tot_ctb_n = "";
    var html_tot_margen = "";
    var html_tot_unidades = "";
    var html = "";
    var html_div_etiquetas = "";
    var anio_th = 0;
    var colspan_anio_th = 0;
    html += "<table class=\"datagrid\" style=\"width:100%;\">";
    html += "<thead>";
    html_div_etiquetas += "<table class=\"datagrid\">";
    html_div_etiquetas += "<thead>";
    html_div_etiquetas += "<tr>";
    html_div_etiquetas += "<th class=\"label\">Año</th>";
    /* Aqui se genera la cabecera TH con los años */
    html += "<tr>";
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
    html_div_etiquetas += "</tr>";
    html_div_etiquetas += "<tr>";
    html_div_etiquetas += "<th class=\"label\">Periodo</th>";
    html += "<tr>";
    for (var x=0; x<data.periodos.length; x++){
        if (data.periodos[x].temporada){
            html += "<th title=\"Periodo de la temporada " 
                + data.temporada_vigente.nombre + " - " 
                + (parseInt(data.temporada_vigente.anio))  
                + "\" style=\"background-color:#F5F5ED;\">" 
                + data.periodos[x].nombre + "</th>";
        }
        else
            html += "<th>" + data.periodos[x].nombre + "</th>";
    }
    html += "</tr>";
    html += "</thead>";
    html += "<tbody>";
    html_div_etiquetas += "</tr>";
    html_div_etiquetas += "</thead>";
    html_div_etiquetas += "<tbody>";
    
    /* Se itera por cada temporada */
    $.each(data.ventas, function(temporada, ventas) {
        html += "<tr>";
        html += "<td class=\"separador\" colspan=\"12\">-</td>";
        html += "</tr>";

        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td class=\"separador\"><b>Temporada: " + temporada + "</b></td>";
        html_div_etiquetas += "</tr>";

        /* Unidades vendidas */
        html += "<tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td title=\"Unidades vendidas.\" class=\"label\">Unidades</td>";

        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par unidades\">" + numeral(venta.vta_u).format('0,0') + "</td>";
        });
        html += "</tr>";
        html_div_etiquetas += "</tr>";
        
         /* Descuentos */
        html += "<tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td title=\"Descuento sobre el precio blanco.\" class=\"label\">Dcto. %</td>";

        $.each(ventas, function(periodo, venta) {
                html += "<td class=\"par descuentos\">" + numeral(venta.dcto).format('0.00%') + "</td>";
        });
        html += "</tr>";
        html_div_etiquetas += "</tr>";

        /* Precio Real */
        html += "<tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td title=\"Precio real de venta.\" class=\"label\">Precio Real</td>";

        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.precio_real).format('0,0') + "</td>";
        });
        html += "</tr>";
        html_div_etiquetas += "</tr>";

        /* Venta neta */
        html += "<tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td title=\"Venta en pesos.\" class=\"label\">Venta</td>";

        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.vta_n).format('0,0') + "</td>";    
        });
        html += "</tr>";
        html_div_etiquetas += "</tr>";
        
         /* Contribucion */
        html += "<tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td title=\"Contribucion en pesos.\" class=\"label\">Contribuci&oacute;n</td>";

        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.ctb_n).format('0,0') + "</td>";
        });
        html += "</tr>";
        html_div_etiquetas += "</tr>";
        
        /* Margen */
        html += "<tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<td title=\"Margen porcentual.\" class=\"label\">Margen %</td>";

        $.each(ventas, function(periodo, venta) {
            html += "<td class=\"par\">" + numeral(venta.margen).format('0.00%') + "</td>";
        });
        html += "</tr>";
        html_div_etiquetas += "</tr>";

    });
    
    /* Totales */
    html += "<tr>";
    html += "<td class=\"separador\" colspan=\"12\">-</td>";
    html += "</tr>";
    html_div_etiquetas += "<tr>";
    html_div_etiquetas += "<td class=\"separador\"><b>Totales:</b></td>";
    html_div_etiquetas += "</tr>";
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
            total_margen = (total_ctb_n / total_vta_n).toFixed(3);
        html_tot_unidades += "<td>" + numeral(total_unidades).format('0,0') + "</td>";
        html_tot_vta_n += "<td>" + numeral(total_vta_n).format('0,0') + "</td>";
        html_tot_ctb_n += "<td>" + numeral(total_ctb_n).format('0,0') + "</td>";
        html_tot_margen += "<td>" + numeral(total_margen).format('0.00%') + "</td>";
    }
    html += "<tr class=\"par totales\">";
    html += html_tot_unidades;
    html += "</tr>";
    html_div_etiquetas += "<tr class=\"totales\">";
    html_div_etiquetas += "<td title=\"Total unidades temporadas.\" class=\"label\">Unidades</td>";
    html_div_etiquetas += "</tr>";

    html += "<tr class=\"par totales\">";
    html += html_tot_vta_n;
    html += "</tr>";
    html_div_etiquetas += "<tr class=\"totales\">";
    html_div_etiquetas += "<td title=\"Total venta temporadas.\" class=\"label\">Venta</td>";
    html_div_etiquetas += "</tr>";

    html += "<tr class=\"par totales\">";
    html += html_tot_ctb_n;
    html += "</tr>";
    html_div_etiquetas += "<tr class=\"totales\">";
    html_div_etiquetas += "<td title=\"Total contribuci&oacute;n.\" class=\"label\">Contribuci&oacute;n</td>";
    html_div_etiquetas += "</tr>";

    html += "<tr class=\"par totales\">";
    html += html_tot_margen;
    html += "</tr>";
    html_div_etiquetas += "<tr class=\"totales\">";
    html_div_etiquetas += "<td title=\"Total margen.\" class=\"label\">Margen</td>";
    html_div_etiquetas += "</tr>";
    
    html += "</tbody>";
    html += "</table>";
    html_div_etiquetas += "</tbody>";
    html_div_etiquetas += "</table>";

    $("#div_etiquetas_comparativo").html(html_div_etiquetas);
    $("#div_datos_comparativo").html(html);
}

function actualizarPlanificacionAS(metrica, periodo, temporada){
    planificacion = obj_trabajo.getDatos();
    // Si se planificaron las unidades, se entra al ciclo if
    if(metrica == 'unidades'){
        $.each(planificacion.ventas[temporada], function(periodo_venta, venta) {
            if(periodo_venta == periodo.trim()){
                // Se asigna tipo temporal 3 (proyectada no guardada)
                venta.tipo = 3;
                // Se lee el valor de la celda y se quita su formato
                venta.vta_u = numeral().unformat(obj_trabajo.getCeldaEditada().text());

                // Venta Neta
                venta.vta_n = parseInt( (1 - venta.dcto) * venta.vta_u * planificacion.itemplan.precio / 1.19 );
                console.log("Venta neta: " + venta.vta_n);
                
                // Contribucion
                venta.ctb_n = parseInt(venta.vta_n - (venta.vta_u * planificacion['itemplan'].costo_unitario));
                console.log("Contribucion neta: " + venta.ctb_n);
                
                // Margen                   
                if(venta.vta_n != 0)
                    venta.margen = (venta.ctb_n / venta.vta_n).toFixed(3);
                console.log("Margen: " + venta.margen);

                // Precio Real
                if(venta.vta_n != 0)
                    venta.precio_real = (venta.vta_n / venta.vta_u * 1.19).toFixed(3);
                console.log("Precio real: " + venta.precio_real);

                // Costo
                venta.costo = parseFloat(venta.vta_u * planificacion['itemplan'].costo_unitario).toFixed(1);

                // Costo Unitario
                venta.costo_unitario = planificacion['itemplan'].costo_unitario

                crearTablaPlanificacionAS(planificacion);
            }
        });
    }
    // Si se planificaron los descuentos, se entra al ciclo if
    else if(metrica == 'descuentos'){
        $.each(planificacion.ventas[temporada], function(periodo_venta, venta) {
            if(periodo_venta == periodo.trim()){
                // Se asigna tipo temporal 3 (proyectada no guardada)
                venta.tipo = 3;
                // Se lee el valor de la celda y se quita su formato
                venta.dcto = numeral().unformat(obj_trabajo.getCeldaEditada().text());
                
                // Venta Neta
                venta.vta_n = parseInt( (1 - venta.dcto) * venta.vta_u * planificacion.itemplan.precio / 1.19 );
                console.log("Venta neta: " + venta.vta_n);
                
                // Contribucion
                venta.ctb_n = parseInt(venta.vta_n - (venta.vta_u * planificacion['itemplan'].costo_unitario));
                console.log("Contribucion neta: " + venta.ctb_n);
                
                // Margen                   
                if(venta.vta_n != 0)
                    venta.margen = (venta.ctb_n / venta.vta_n).toFixed(3);
                console.log("Margen: " + venta.margen);

                // Precio Real
                if(venta.vta_n != 0)
                    venta.precio_real = (venta.vta_n / venta.vta_u * 1.19).toFixed(3);
                console.log("Precio real: " + venta.precio_real);

                // Costo
                venta.costo = parseFloat(venta.vta_u * planificacion['itemplan'].costo_unitario).toFixed(1);

                // Costo Unitario
                venta.costo_unitario = planificacion['itemplan'].costo_unitario

                crearTablaPlanificacionAS(planificacion);
                return false;
            }
        });
    }
    obj_trabajo.setDatos(planificacion);
}