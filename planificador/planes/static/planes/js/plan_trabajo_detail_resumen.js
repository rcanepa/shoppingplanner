/*
Construye los graficos de resumen asociados al elemento escogido por
el usuario.
*/
function busquedaResumen(data){
	console.log(data);
    var data_unidades = data.estadisticas.unidades;
    var data_venta = data.estadisticas.venta;
    var data_contribucion = data.estadisticas.contribucion;
    var data_margen = data.estadisticas.margen;
    var data_costo = data.estadisticas.costo;
    var data_dcto_precio = data.estadisticas.dcto_precio;

    var colores_arr = ['#44bbcc','#88dddd','#bbeeff'];
    var color_linea_margen = ['#0055bb'];
    var color_texto = '#777';
    var tipo_letra = "Sans-Serif";
    var tamano_letra = 10;

    // Reset the canvas
	RGraph.Reset(document.getElementById("venta-chart"));
	RGraph.Reset(document.getElementById("unidades-chart"));
	RGraph.Reset(document.getElementById("contribucion-chart"));
    RGraph.Reset(document.getElementById("margen-chart"));
	RGraph.Reset(document.getElementById("precio-chart"));

    var bar_venta = new RGraph.Bar('venta-chart', data_venta.rows)
        .Set('text.color', color_texto)
        /*.Set('text.font', tipo_letra)*/
        .Set('labels', data_venta.cols)
        .Set('labels.above', true)
        .Set('labels.above.size', tamano_letra)
        .Set('colors', colores_arr)
        .Set('ylabels', false)
        .Set('noyaxis', true)
        .Set('gutter.left', 10)
        .Set('gutter.right', 10)
        .Set('background.grid', false)
        .Set('labels.ingraph', data_venta.ingraph)
        .Draw();

    var bar_unidades = new RGraph.Bar('unidades-chart', data_unidades.rows)
        .Set('text.color', color_texto)
        .Set('labels', data_unidades.cols)
        .Set('labels.above', true)
        .Set('labels.above.size', tamano_letra)
        .Set('colors', colores_arr)
        .Set('ylabels', false)
        .Set('noyaxis', true)
        .Set('gutter.left', 10)
        .Set('gutter.right', 10)
        .Set('background.grid', false)
        .Set('labels.ingraph', data_unidades.ingraph)
        .Draw();

    var bar_contribucion = new RGraph.Bar('contribucion-chart', data_contribucion.rows)
        .Set('text.color', color_texto)
        /*.Set('tooltips', data_contribucion.tooltips)
        .Set('tooltips.event','onmousemove')*/
        .Set('labels', data_contribucion.cols)
        .Set('labels.above', true)
        .Set('labels.above.size', tamano_letra)
        .Set('colors', colores_arr)
        .Set('ylabels', false)
        .Set('noyaxis', true)
        .Set('gutter.left', 10)
        .Set('gutter.right', 10)
        .Set('background.grid', false)
        .Set('labels.ingraph', data_contribucion.ingraph)

    var line_margen = new RGraph.Line('margen-chart', data_margen.rows)
        /*.Set('tooltips', data_margen.tooltips)
        .Set('tooltips.hotspot.size', 20)*/
        .Set('text.color', color_texto)
        /*.Set('labels.above', true)
        .Set('labels.above.size', tamano_letra)*/
        .Set('colors', color_linea_margen)
        .Set('tickmarks', 'circle')
        .Set('ylabels', false)
        .Set('noyaxis', true)
        .Set('linewidth', 2)
        .Set('units.post', '%')
        .Set('gutter.left', 10)
        .Set('gutter.right', 10)
        .Set('background.grid', false)
		.Set('outofbounds', true) // Para valores negativos
        .Set('labels.ingraph', data_margen.ingraph)
    var combo = new RGraph.CombinedChart(bar_contribucion, line_margen);
	combo.Draw();

    var bar_precio_dcto = new RGraph.Bar('precio-chart', data_dcto_precio.rows)
        .Set('text.color', color_texto)
        .Set('colors', colores_arr)
        .Set('labels', data_dcto_precio.cols)
        .Set('labels.above', true)
        .Set('labels.above.size', tamano_letra)
        .Set('grouping', 'stacked')
        .Set('noyaxis', true)
        .Set('gutter.left', 10)
        .Set('gutter.right', 10)
        .Set('background.grid', false)
        .Set('ylabels', false)
        .Set('linewidth', 2)
		.Set('strokestyle', 'white')
        .Draw();

    // Esta funcion se utiliza para unificar los pedazos de cada barra, con el objetivo de que
    // los tooltips se muestren al pasar el mouse sobre cualquiera de ellos
    RGraph.each (bar_precio_dcto.coords2, function (key, value)
    {
        var x = value[0][0];
        var y = value[0][1];
        var w = value[0][2];
        var h = value[0][3] + value[1][3] + value[2][3]; // Sum up the heights of the bar segments

        var rect = new RGraph.Drawing.Rect('precio-chart', x, y, w, h)
            .Set('strokestyle', 'rgba(0,0,0,0)')
            .Set('fillstyle', 'rgba(0,0,0,0)')
            /*.Set('tooltips', [data_dcto_precio.tooltips[key]])
            .Set('tooltips.event','onmousemove')*/
            .Set('highlight.stroke', 'rgba(0,0,0,0)')
            .Draw();
    }, bar_precio_dcto);

    var bar_costo = new RGraph.Bar('precio-chart', data_costo.rows)
        .Set('text.color', color_texto)
        .Set('ymax', bar_precio_dcto.scale2.max)
        .Set('gutter.left', bar_precio_dcto.Get('gutter.left'))
        .Set('colors', color_linea_margen)
        .Set('noaxes', true)
        .Set('labels.above', true)
        .Set('labels.above.size', tamano_letra)
        .Set('hmargin', 20)
        .Set('ylabels', false)
        .Set('noyaxis', true)
        .Set('gutter.left', 10)
        .Set('gutter.right', 10)
        .Set('background.grid', false)
        .Draw();
}

/*
Construye los graficos de resumen comparativo asociados al elemento escogido por
el usuario.
*/
function busquedaResumenComp(data){
	console.log(data);
    var data_unidades = data.estadisticas.unidades;
    var data_venta = data.estadisticas.venta;
    var data_contribucion = data.estadisticas.contribucion;
    var data_margen = data.estadisticas.margen;
    var data_costo = data.estadisticas.costo;
    var data_dcto_precio = data.estadisticas.dcto_precio;

    var colores_arr = ['#44bbcc','#88dddd','#bbeeff'];
    var color_linea_margen = ['#0055bb'];
    var color_texto = '#777';
    var tipo_letra = "Sans-Serif";
    var tamano_letra = 10;

    // Reset the canvas
	RGraph.Reset(document.getElementById("venta-chart-comp"));
	RGraph.Reset(document.getElementById("unidades-chart-comp"));
	RGraph.Reset(document.getElementById("contribucion-chart-comp"));
    RGraph.Reset(document.getElementById("margen-chart-comp"));
	RGraph.Reset(document.getElementById("precio-chart-comp"));

    var bar_venta = new RGraph.Bar('venta-chart-comp', data_venta.rows)
        .Set('text.color', color_texto)
        //.Set('text.font', tipo_letra)
        .Set('labels', data_venta.cols)
        .Set('labels.above', true)
        .Set('labels.above.size', tamano_letra)
        .Set('colors', colores_arr)
        .Set('ylabels', false)
        .Set('noyaxis', true)
        .Set('gutter.left', 10)
        .Set('gutter.right', 10)
        .Set('background.grid', false)
        .Set('labels.ingraph', data_venta.ingraph)
        .Draw();

    var bar_unidades = new RGraph.Bar('unidades-chart-comp', data_unidades.rows)
        .Set('text.color', color_texto)
        .Set('labels', data_unidades.cols)
        .Set('labels.above', true)
        .Set('labels.above.size', tamano_letra)
        .Set('colors', colores_arr)
        .Set('ylabels', false)
        .Set('noyaxis', true)
        .Set('gutter.left', 10)
        .Set('gutter.right', 10)
        .Set('background.grid', false)
        .Set('labels.ingraph', data_unidades.ingraph)
        .Draw();

    var bar_contribucion = new RGraph.Bar('contribucion-chart-comp', data_contribucion.rows)
        .Set('text.color', color_texto)
        /*.Set('tooltips', data_contribucion.tooltips)
        .Set('tooltips.event','onmousemove')*/
        .Set('labels', data_contribucion.cols)
        .Set('labels.above', true)
        .Set('labels.above.size', tamano_letra)
        .Set('colors', colores_arr)
        .Set('ylabels', false)
        .Set('noyaxis', true)
        .Set('gutter.left', 10)
        .Set('gutter.right', 10)
        .Set('background.grid', false)
        .Set('labels.ingraph', data_contribucion.ingraph)

    var line_margen = new RGraph.Line('margen-chart-comp', data_margen.rows)
        /*.Set('tooltips', data_margen.tooltips)
        .Set('tooltips.hotspot.size', 20)*/
        .Set('colors', color_linea_margen)
        .Set('tickmarks', 'circle')
        .Set('ylabels', false)
        .Set('noyaxis', true)
        .Set('linewidth', 2)
        .Set('units.post', '%')
        .Set('gutter.left', 10)
        .Set('gutter.right', 10)
		.Set('outofbounds', true) // Para valores negativos
        .Set('labels.ingraph', data_margen.ingraph)
    var combo = new RGraph.CombinedChart(bar_contribucion, line_margen);
	combo.Draw();

    var bar_precio_dcto = new RGraph.Bar('precio-chart-comp', data_dcto_precio.rows)
        .Set('text.color', color_texto)
        .Set('colors', colores_arr)
        .Set('labels', data_dcto_precio.cols)
        .Set('labels.above', true)
        .Set('labels.above.size', tamano_letra)
        .Set('grouping', 'stacked')
        .Set('noyaxis', true)
        .Set('gutter.left', 10)
        .Set('gutter.right', 10)
        .Set('background.grid', false)
        .Set('ylabels', false)
        .Set('linewidth', 2)
		.Set('strokestyle', 'white')
        .Draw();

    // Esta funcion se utiliza para unificar los pedazos de cada barra, con el objetivo de que
    // los tooltips se muestren al pasar el mouse sobre cualquiera de ellos
    RGraph.each (bar_precio_dcto.coords2, function (key, value)
    {
        var x = value[0][0];
        var y = value[0][1];
        var w = value[0][2];
        var h = value[0][3] + value[1][3] + value[2][3]; // Sum up the heights of the bar segments

        var rect = new RGraph.Drawing.Rect('precio-chart-comp', x, y, w, h)
            .Set('strokestyle', 'rgba(0,0,0,0)')
            .Set('fillstyle', 'rgba(0,0,0,0)')
            /*.Set('tooltips', [data_dcto_precio.tooltips[key]])
            .Set('tooltips.event','onmousemove')*/
            .Set('highlight.stroke', 'rgba(0,0,0,0)')
            .Draw();
    }, bar_precio_dcto);

    var bar_costo = new RGraph.Bar('precio-chart-comp', data_costo.rows)
        .Set('text.color', color_texto)
        .Set('ymax', bar_precio_dcto.scale2.max)
        .Set('gutter.left', bar_precio_dcto.Get('gutter.left'))
        .Set('colors', color_linea_margen)
        .Set('noaxes', true)
        .Set('labels.above', true)
        .Set('labels.above.size', tamano_letra)
        .Set('hmargin', 20)
        .Set('ylabels', false)
        .Set('noyaxis', true)
        .Set('gutter.left', 10)
        .Set('gutter.right', 10)
        .Set('background.grid', false)
        .Draw();
}