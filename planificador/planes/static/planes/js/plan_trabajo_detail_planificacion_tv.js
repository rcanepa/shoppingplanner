/*
Recibe la respuesta tipo AJAX que se genera al seleccionar un item a proyectar.
*/
function busquedaPlanificacionTV(data){
    /* Se revisa que la busqueda haya devuelto ventas. */
    if( data.ventas != null ){
        $("#itemprecio_blanco").text(numeral(data.itemplan.precio).format('0,0'));
        $("#itemcosto_unitario").text(numeral(data.itemplan.costo_unitario).format('0,0'));
        obj_trabajo.setPlanificacion(data);
        //actualizarPlanificacion();
        crearTablaPlanificacionTV(data);
    }
    else{
        alert("El item seleccionado no es válido. Por favor verifique que haya escogido correctamente un item y que tenga los permisos necesarios para verlo");
    }
}

function crearTablaPlanificacionTV(data){

        var html_num_periodos = 6;
        var html_tot_vta_n = "";
        var html_tot_ctb_n = "";
        var html_tot_margen = "";
        var html_tot_unidades = "";
        var html = "";
        var html_div_etiquetas = "";

        html += "<table class=\"datagrid\">";
        html += "<thead>";
        html += "<tr>";
        html_div_etiquetas += "<table class=\"datagrid\">";
        html_div_etiquetas += "<thead>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<th class=\"label\">Año</th>";
        // Se genera la cabecera con los años
        for (var x=0; x<data.periodos.length; x++){
            if ( (x % html_num_periodos) == 0 ){
                if ( data.periodos[x].temporada ){
                    if ( (x % html_num_periodos) == 0 )
                    html += "<th colspan=\"" + html_num_periodos + "\">" + data.periodos[x].tiempo__anio + "</th>";
                }
                else{
                    if ( (data.periodos[x].tiempo__anio % 2) == 0 )
                        html += "<th colspan=\"" + html_num_periodos + "\">" + data.periodos[x].tiempo__anio + "</th>";
                    else
                        html += "<th colspan=\"" + html_num_periodos + "\">" + data.periodos[x].tiempo__anio + "</th>";
                }
            }
        }
        html += "</tr>";
        html += "<tr>";
        html_div_etiquetas += "</tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<th class=\"label\">Periodo</th>";
        // Se genera la fila con los periodos
        for (var x=0; x<data.periodos.length; x++){
            if ( data.periodos[x].temporada ){
                html += "<th class=\"plan\">" + data.periodos[x].nombre + "</th>";
            }
            else{
                if ( (data.periodos[x].tiempo__anio % 2) == 0 )
                    html += "<th class=\"par\">" + data.periodos[x].nombre + "</th>";
                else
                    html += "<th class=\"impar\">" + data.periodos[x].nombre + "</th>";
            }
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
            html += "<td class=\"separador\" colspan=\"24\">-</td>";
            html += "</tr>";

            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td class=\"separador\"><b>Temporada: " + temporada + "</b></td>";
            html_div_etiquetas += "</tr>";

            /* Unidades vendidas */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Unidades vendidas.\" class=\"label\">Unidades</td>";

            $.each(ventas, function(periodo, venta) {
                if( venta.anio == (data.temporada_vigente['anio']) )
                    html += "<td id=\"unidades_" + venta.anio + "" + venta.periodo + "_" + temporada + "\" class=\"unidades editable plan\">" + numeral(venta.vta_u).format('0,0') + "</td>";
                else{
                    if ( (venta.anio % 2) == 0 )
                        html += "<td class=\"par\">" + numeral(venta.vta_u).format('0,0') + "</td>";
                    else
                        html += "<td class=\"impar\">" + numeral(venta.vta_u).format('0,0') + "</td>";
                }
                    

            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";
            
            /* Descuentos */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Descuento sobre el precio blanco.\" class=\"label\">Dcto. %</td>";
            $.each(ventas, function(periodo, venta) {
                if( venta.anio == (data.temporada_vigente['anio']) )
                    html += "<td id=\"descuentos_" + venta.anio + "" + venta.periodo + "_" + temporada + "\" class=\"descuentos editable plan\">" + numeral(venta.dcto).format('0.00%') + "</td>";
                else{
                    if ( (venta.anio % 2) == 0 )
                        html += "<td class=\"par\">" + numeral(venta.dcto).format('0.00%') + "</td>";
                    else
                        html += "<td class=\"impar\">" + numeral(venta.dcto).format('0.00%') + "</td>";
                }
                    
            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";

            /* Precio Real */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Precio real de venta.\" class=\"label\">Precio Real</td>";
            $.each(ventas, function(periodo, venta) {
                if ( (venta.anio % 2) == 0 )
                    html += "<td class=\"par\">" + numeral(venta.precio_real).format('0,0') + "</td>";
                else
                    html += "<td class=\"impar\">" + numeral(venta.precio_real).format('0,0') + "</td>";    
            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";

            /* Costo unitario */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Costo unitario.\" class=\"label\">Costo Uni.</td>";
            $.each(ventas, function(periodo, venta) {
                if ( (venta.anio % 2) == 0 )
                    html += "<td class=\"par\">" + numeral(venta.costo_u).format('0,0') + "</td>";
                else
                    html += "<td class=\"impar\">" + numeral(venta.costo_u).format('0,0') + "</td>";
                    
            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";

            /* Venta neta */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Venta en pesos.\" class=\"label\">Venta</td>";
            $.each(ventas, function(periodo, venta) {
                if ( (venta.anio % 2) == 0 )
                    html += "<td class=\"par\">" + numeral(venta.vta_n).format('0,0') + "</td>";
                else
                    html += "<td class=\"impar\">" + numeral(venta.vta_n).format('0,0') + "</td>";    
            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";
            
             /* Contribucion */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Contribucion en pesos.\" class=\"label\">Contribuci&oacute;n</td>";
            $.each(ventas, function(periodo, venta) {
                if ( (venta.anio % 2) == 0 )
                    html += "<td class=\"par\">" + numeral(venta.ctb_n).format('0,0') + "</td>";
                else
                    html += "<td class=\"impar\">" + numeral(venta.ctb_n).format('0,0') + "</td>";
            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";
            
            /* Margen */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Margen porcentual.\" class=\"label\">Margen %</td>";
            $.each(ventas, function(periodo, venta) {
                if ( (venta.anio % 2) == 0 )
                    html += "<td class=\"par\">" + numeral(venta.margen).format('0.00%') + "</td>";
                else
                    html += "<td class=\"impar\">" + numeral(venta.margen).format('0.00%') + "</td>";
            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";

        });
        
        /* Totales */
        html += "<tr>";
        html += "<td class=\"separador\" colspan=\"24\">-</td>";
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
                    if (periodo == (data.periodos[x].tiempo__anio + " " + data.periodos[x].nombre)){
                        total_unidades += parseFloat(venta.vta_u);
                        total_vta_n += parseFloat(venta.vta_n);
                        total_ctb_n += parseFloat(venta.ctb_n);
                        return false;
                    }
                });

            });
            if (total_vta_n != 0)
                total_margen = total_ctb_n / total_vta_n;
            if ( (data.periodos[x].tiempo__anio % 2) == 0 ){
                html_tot_unidades += "<td class=\"par\">" + numeral(total_unidades).format('0,0') + "</td>";
                html_tot_vta_n += "<td class=\"par\">" + numeral(total_vta_n).format('0,0') + "</td>";
                html_tot_ctb_n += "<td class=\"par\">" + numeral(total_ctb_n).format('0,0') + "</td>";
                html_tot_margen += "<td class=\"par\">" + numeral(total_margen).format('0.00%') + "</td>";
            }
            else{
                html_tot_unidades += "<td class=\"impar\">" + numeral(total_unidades).format('0,0') + "</td>";
                html_tot_vta_n += "<td class=\"impar\">" + numeral(total_vta_n).format('0,0') + "</td>";
                html_tot_ctb_n += "<td class=\"impar\">" + numeral(total_ctb_n).format('0,0') + "</td>";
                html_tot_margen += "<td class=\"impar\">" + numeral(total_margen).format('0.00%') + "</td>";
            }
        }
        
        html += "<tr class=\"totales\">";
        html += html_tot_unidades;
        html += "</tr>";
        html_div_etiquetas += "<tr class=\"totales\">";
        html_div_etiquetas += "<td title=\"Total unidades temporadas.\" class=\"label\">Unidades</td>";
        html_div_etiquetas += "</tr>";

        html += "<tr class=\"totales\">";
        html += html_tot_vta_n;
        html += "</tr>";
        html_div_etiquetas += "<tr class=\"totales\">";
        html_div_etiquetas += "<td title=\"Total venta temporadas.\" class=\"label\">Venta</td>";
        html_div_etiquetas += "</tr>";

        html += "<tr class=\"totales\">";
        html += html_tot_ctb_n;
        html += "</tr>";
        html_div_etiquetas += "<tr class=\"totales\">";
        html_div_etiquetas += "<td title=\"Total contribuci&oacute;n.\" class=\"label\">Contribuci&oacute;n</td>";
        html_div_etiquetas += "</tr>";

        html += "<tr class=\"totales\">";
        html += html_tot_margen;
        html += "</tr>";
        html_div_etiquetas += "<tr class=\"totales\">";
        html_div_etiquetas += "<td title=\"Total margen.\" class=\"label\">Margen</td>";
        html_div_etiquetas += "</tr>";

        html += "</tbody>";
        html += "</table>";
        html_div_etiquetas += "</tbody>";
        html_div_etiquetas += "</table>";
        $("#tab_planificacion_datos").html(html);
        $("#tab_planificacion_etiquetas").html(html_div_etiquetas);
        //$(".editable").click(planificarMetricas);
    }

    function crearTablaPlanificacionTVComp(data){

        var html_num_periodos = 6;
        var html_tot_vta_n = "";
        var html_tot_ctb_n = "";
        var html_tot_margen = "";
        var html_tot_unidades = "";
        var html = "";        
        var html_div_etiquetas = "";

        html += "<table class=\"datagrid\">";
        html += "<thead>";
        html += "<tr>";
        html_div_etiquetas += "<table class=\"datagrid\">";
        html_div_etiquetas += "<thead>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<th class=\"label\">Año</th>";
        // Se genera la cabecera con los años
        for (var x=0; x<data.periodos.length; x++){
            if ( (x % html_num_periodos) == 0 ){
                if ( data.periodos[x].temporada ){
                    if ( (x % html_num_periodos) == 0 )
                    html += "<th colspan=\"" + html_num_periodos + "\">" + data.periodos[x].tiempo__anio + "</th>";
                }
                else{
                    if ( (data.periodos[x].tiempo__anio % 2) == 0 )
                        html += "<th colspan=\"" + html_num_periodos + "\">" + data.periodos[x].tiempo__anio + "</th>";
                    else
                        html += "<th colspan=\"" + html_num_periodos + "\">" + data.periodos[x].tiempo__anio + "</th>";
                }
            }
        }
        html += "</tr>";
        html += "<tr>";
        html_div_etiquetas += "</tr>";
        html_div_etiquetas += "<tr>";
        html_div_etiquetas += "<th class=\"label\">Periodo</th>";
        // Se genera la fila con los periodos
        for (var x=0; x<data.periodos.length; x++){
            if ( data.periodos[x].temporada ){
                html += "<th class=\"plan\">" + data.periodos[x].nombre + "</th>";
            }
            else{
                if ( (data.periodos[x].tiempo__anio % 2) == 0 )
                    html += "<th class=\"par\">" + data.periodos[x].nombre + "</th>";
                else
                    html += "<th class=\"impar\">" + data.periodos[x].nombre + "</th>";
            }
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
            html += "<td class=\"separador\" colspan=\"24\">-</td>";
            html += "</tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td class=\"separador\"><b>Temporada: " + temporada + "</b></td>";
            html_div_etiquetas += "</tr>";

            /* Unidades vendidas */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Unidades vendidas.\" class=\"label\">Unidades</td>";
            $.each(ventas, function(periodo, venta) {
                if( venta.anio == (data.temporada_vigente['anio']) )
                    html += "<td id=\"unidades_" + venta.anio + "" + venta.periodo + "_" + temporada + "\" class=\"unidades plan\">" + numeral(venta.vta_u).format('0,0') + "</td>";
                else{
                    if ( (venta.anio % 2) == 0 )
                        html += "<td class=\"par\">" + numeral(venta.vta_u).format('0,0') + "</td>";
                    else
                        html += "<td class=\"impar\">" + numeral(venta.vta_u).format('0,0') + "</td>";
                }
                    

            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";
            
            /* Descuentos */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Descuento sobre el precio blanco.\" class=\"label\">Descuento %</td>";
            $.each(ventas, function(periodo, venta) {
                if( venta.anio == (data.temporada_vigente['anio']) )
                    html += "<td id=\"descuentos_" + venta.anio + "" + venta.periodo + "_" + temporada + "\" class=\"descuentos plan\">" + numeral(venta.dcto).format('0.00%') + "</td>";
                else{
                    if ( (venta.anio % 2) == 0 )
                        html += "<td class=\"par\">" + numeral(venta.dcto).format('0.00%') + "</td>";
                    else
                        html += "<td class=\"impar\">" + numeral(venta.dcto).format('0.00%') + "</td>";
                }
                    
            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";

            /* Precio Real */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Precio real de venta.\" class=\"label\">Precio Real</td>";
            $.each(ventas, function(periodo, venta) {
                if( venta.anio == (data.temporada_vigente['anio']) )
                    html += "<td class=\"plan\">" + numeral(venta.precio_real).format('0,0') + "</td>";
                else{
                    if ( (venta.anio % 2) == 0 )
                        html += "<td class=\"par\">" + numeral(venta.precio_real).format('0,0') + "</td>";
                    else
                        html += "<td class=\"impar\">" + numeral(venta.precio_real).format('0,0') + "</td>";    
                }
            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";

            /* Costo unitario */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Costo unitario.\" class=\"label\">Costo Unitario</td>";
            $.each(ventas, function(periodo, venta) {
                if( venta.anio == (data.temporada_vigente['anio']) )
                    html += "<td id=\"costos_" + venta.anio + "" + venta.periodo + "_" + temporada + "\" class=\"costos plan\">" + numeral(venta.costo_u).format('0,0') + "</td>";
                else{
                    if ( (venta.anio % 2) == 0 )
                        html += "<td class=\"par\">" + numeral(venta.costo_u).format('0,0') + "</td>";
                    else
                        html += "<td class=\"impar\">" + numeral(venta.costo_u).format('0,0') + "</td>";
                }
                    
            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";

            /* Venta neta */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Venta en pesos.\" class=\"label\">Venta</td>";
            $.each(ventas, function(periodo, venta) {
                if( venta.anio == (data.temporada_vigente['anio']) )
                    html += "<td class=\"plan\">" + numeral(venta.vta_n).format('0,0') + "</td>";
                else{
                    if ( (venta.anio % 2) == 0 )
                        html += "<td class=\"par\">" + numeral(venta.vta_n).format('0,0') + "</td>";
                    else
                        html += "<td class=\"impar\">" + numeral(venta.vta_n).format('0,0') + "</td>";    
                }
            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";
            
             /* Contribucion */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Contribucion en pesos.\" class=\"label\">Contribuci&oacute;n</td>";
            $.each(ventas, function(periodo, venta) {
                if( venta.anio == (data.temporada_vigente['anio']) )
                    html += "<td class=\"plan\">" + numeral(venta.ctb_n).format('0,0') + "</td>";
                else{
                    if ( (venta.anio % 2) == 0 )
                        html += "<td class=\"par\">" + numeral(venta.ctb_n).format('0,0') + "</td>";
                    else
                        html += "<td class=\"impar\">" + numeral(venta.ctb_n).format('0,0') + "</td>";
                }
            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";

            /* Margen */
            html += "<tr>";
            html_div_etiquetas += "<tr>";
            html_div_etiquetas += "<td title=\"Margen porcentual.\" class=\"label\">Margen %</td>";
            $.each(ventas, function(periodo, venta) {
                if( venta.anio == (data.temporada_vigente['anio']) )
                    html += "<td class=\"plan\">" + numeral(venta.margen).format('0.00%') + "</td>";
                else{
                    if ( (venta.anio % 2) == 0 )
                        html += "<td class=\"par\">" + numeral(venta.margen).format('0.00%') + "</td>";
                    else
                        html += "<td class=\"impar\">" + numeral(venta.margen).format('0.00%') + "</td>";
                }
            });
            html += "</tr>";
            html_div_etiquetas += "</tr>";

        });
        
        /* Totales */
        html += "<tr>";
        html += "<td class=\"separador\" colspan=\"24\">-</td>";
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
                    if (periodo == (data.periodos[x].tiempo__anio + " " + data.periodos[x].nombre)){
                        total_unidades += parseFloat(venta.vta_u);
                        total_vta_n += parseFloat(venta.vta_n);
                        total_ctb_n += parseFloat(venta.ctb_n);
                        return false;
                    }
                });

            });
            if (total_vta_n != 0)
                total_margen = total_ctb_n / total_vta_n;
            if ( data.periodos[x].temporada ){
                html_tot_unidades += "<td class=\"plan\">" + numeral(total_unidades).format('0,0') + "</td>";
                html_tot_vta_n += "<td class=\"plan\">" + numeral(total_vta_n).format('0,0') + "</td>";
                html_tot_ctb_n += "<td class=\"plan\">" + numeral(total_ctb_n).format('0,0') + "</td>";
                html_tot_margen += "<td class=\"plan\">" + numeral(total_margen).format('0.00%') + "</td>";
            }
            else{
                if ( (data.periodos[x].tiempo__anio % 2) == 0 ){
                    html_tot_unidades += "<td class=\"par\">" + numeral(total_unidades).format('0,0') + "</td>";
                    html_tot_vta_n += "<td class=\"par\">" + numeral(total_vta_n).format('0,0') + "</td>";
                    html_tot_ctb_n += "<td class=\"par\">" + numeral(total_ctb_n).format('0,0') + "</td>";
                    html_tot_margen += "<td class=\"par\">" + numeral(total_margen).format('0.00%') + "</td>";
                }
                else{
                    html_tot_unidades += "<td class=\"impar\">" + numeral(total_unidades).format('0,0') + "</td>";
                    html_tot_vta_n += "<td class=\"impar\">" + numeral(total_vta_n).format('0,0') + "</td>";
                    html_tot_ctb_n += "<td class=\"impar\">" + numeral(total_ctb_n).format('0,0') + "</td>";
                    html_tot_margen += "<td class=\"impar\">" + numeral(total_margen).format('0.00%') + "</td>";
                }
            }
        }
        html += "<tr class=\"totales\">";
        html += html_tot_unidades;
        html += "</tr>";
        html_div_etiquetas += "<tr class=\"totales\">";
        html_div_etiquetas += "<td title=\"Total unidades temporadas.\" class=\"label\">Unidades</td>";
        html_div_etiquetas += "</tr>";

        html += "<tr class=\"totales\">";
        html += html_tot_vta_n;
        html += "</tr>";
        html_div_etiquetas += "<tr class=\"totales\">";
        html_div_etiquetas += "<td title=\"Total venta temporadas.\" class=\"label\">Venta</td>";
        html_div_etiquetas += "</tr>";

        html += "<tr class=\"totales\">";
        html += html_tot_ctb_n;
        html += "</tr>";
        html_div_etiquetas += "<tr class=\"totales\">";
        html_div_etiquetas += "<td title=\"Total contribuci&oacute;n.\" class=\"label\">Contribuci&oacute;n</td>";
        html_div_etiquetas += "</tr>";

        html += "<tr class=\"totales\">";
        html += html_tot_margen;
        html += "</tr>";
        html_div_etiquetas += "<tr class=\"totales\">";
        html_div_etiquetas += "<td title=\"Total margen.\" class=\"label\">Margen</td>";
        html_div_etiquetas += "</tr>";

        html += "</tbody>";
        html += "</table>";
        html_div_etiquetas += "</tbody>";
        html_div_etiquetas += "</table>";
        $("#tab_comparativo_etiquetas").html(html_div_etiquetas);
        $("#tab_comparativo_datos").html(html);
    }
