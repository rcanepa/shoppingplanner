/*
Construye los graficos de resumen asociados al elemento escogido por
el usuario.
*/
function busquedaResumen(data){
	console.log(data);
  for(x=0; x<data.estadisticas.contribucion.rows.length; x++){
      if ( data.estadisticas.contribucion.rows[x][0] < 0 )
          data.estadisticas.contribucion.rows[x][0] = 0;
      if ( data.estadisticas.costo.rows[x] < 0 )
          data.estadisticas.costo.rows[x] = [0];
      for(k=0; k<data.estadisticas.dcto_precio.rows[x].length; k++){
          if ( data.estadisticas.dcto_precio.rows[x][k] < 0 )
              data.estadisticas.dcto_precio.rows[x][k] = [0];
      }
  }
    var data_unidades = data.estadisticas.unidades;
    var data_venta = data.estadisticas.venta;
    var data_contribucion = data.estadisticas.contribucion;
    var data_margen = data.estadisticas.margen;
    var data_costo = data.estadisticas.costo;
    var data_dcto_precio = data.estadisticas.dcto_precio;

    var colores_arr = ['#44bbcc','#88dddd','#bbeeff'];
    var color_linea_margen = ['#0055bb'];
    var color_texto = 'black';
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
        .Set('background.grid', false);
    bar_venta.ondraw = function (obj)
        {
            for (var i=0; i<obj.coords.length; ++i) {
                obj.context.fillStyle = color_texto;
                if ( data_venta.ingraph[i] != null ) {
                    RGraph.Text2(obj.context, {
                       //font:tipo_letra,
                       //'size':tamano_letra,
                       'x':obj.coords[i][0] + (obj.coords[i][2] / 2),
                       'y':obj.coords[i][1] + (obj.coords[i][3] / 2),
                       'text':data_venta.ingraph[i][0],
                       'valign':'center',
                       'halign':'center'
                    });    
                }
            }
        };
    bar_venta.Draw();

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
        .Set('background.grid', false);
    bar_unidades.ondraw = function (obj)
        {
            for (var i=0; i<obj.coords.length; ++i) {
                obj.context.fillStyle = color_texto;
                if ( data_unidades.ingraph[i] != null ) {
                    RGraph.Text2(obj.context, {
                       //font:tipo_letra,
                       //'size':tamano_letra,
                       'x':obj.coords[i][0] + (obj.coords[i][2] / 2),
                       'y':obj.coords[i][1] + (obj.coords[i][3] / 2),
                       'text':data_unidades.ingraph[i][0],
                       'valign':'center',
                       'halign':'center'
                    });    
                }
            }
        };
    bar_unidades.Draw();

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
        .Set('background.grid', false);
    bar_contribucion.ondraw = function (obj) {
        for (var i=0; i<obj.coords.length; ++i) {
            obj.context.fillStyle = color_texto;
            if ( data_contribucion.ingraph[i] != null ) {
                RGraph.Text2(obj.context, {
                   //font:tipo_letra,
                   //'size':tamano_letra,
                   'x':obj.coords[i][0] + (obj.coords[i][2] / 2),
                   'y':obj.coords[i][1] + (obj.coords[i][3] / 2),
                   'text':data_contribucion.ingraph[i][0],
                   'valign':'center',
                   'halign':'center'
                });    
            }
        }
    };

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
		.Set('outofbounds', true);
    line_margen.ondraw = function (obj) {
        for (var i=0; i<obj.coords.length; ++i) {
            obj.context.fillStyle = color_texto;
            if ( data_margen.ingraph[i] != null ) {
                RGraph.Text2(obj.context, {
                   //font:tipo_letra,
                   //'size':tamano_letra,
                   'x':obj.coords[i][0],
                   'y':obj.coords[i][1] - 10,
                   'text':data_margen.ingraph[i][0],
                   'valign':'center',
                   'halign':'center'
                });    
            }
        }
    };
    var combo = new RGraph.CombinedChart(bar_contribucion, line_margen);
	combo.Draw();

    var bar_precio_dcto = new RGraph.Bar('precio-chart', data_dcto_precio.rows)
            .Set('text.color', color_texto)
            .Set('colors', colores_arr)
            .Set('labels', data_dcto_precio.cols)
            .Set('hmargin', 20)
            .Set('grouping', 'stacked')
            .Set('noyaxis', true)          
            .Set('background.grid', false)
            .Set('ylabels', false)
            .Set('linewidth', 2)
            .Set('strokestyle', 'white');
            
        bar_precio_dcto.ondraw = function (obj)
            {
                /* Se agregan los valores por el costado izquierdo de cada barra. */
                for (var j=0; j<data_dcto_precio.labels_aux.length; ++j) {
                    obj.context.fillStyle = color_texto;
                    for (var i=0; i<data_dcto_precio.labels_aux[j].length; ++i) {
                        RGraph.Text2(obj.context, {
                                                   /*font:tipo_letra,
                                                   'size':tamano_letra,*/
                                                   'x':obj.coords2[j][i+1][0] + obj.coords2[j][i+1][2],
                                                   'y':obj.coords2[j][i+1][1],
                                                   'text':numeral(data_dcto_precio.labels_aux[j][i]).format('0,0'),
                                                   'valign':'center',
                                                   'halign':'left'
                                                  });
                    }
                }
                /* Se agregan los totales de cada barra por sobre la barra completa. */
                for (var i=0; i<obj.coords2.length; ++i) {
                    obj.context.fillStyle = color_texto;
                    RGraph.Text2(obj.context, {
                                               /*font:tipo_letra,
                                               'size':tamano_letra,*/
                                               'x':obj.coords2[i][0][0] + (obj.coords2[i][0][2] / 2),
                                               'y':obj.coords2[i][0][1] - 7,
                                               'text':numeral(data_dcto_precio.labels[i]).format('0,0'),
                                               'valign':'center',
                                               'halign':'center'
                                              });
                }
            };
        bar_precio_dcto.Draw();
        

        var bar_costo = new RGraph.Bar('precio-chart', data_costo.rows)
            .Set('text.color', color_texto)
            .Set('ymax', bar_precio_dcto.scale2.max)
            
            .Set('colors', color_linea_margen)
            .Set('noaxes', true)
            .Set('hmargin', 32)
            .Set('ylabels', false)
            .Set('noyaxis', true)
            
            
            .Set('background.grid', false);
        bar_costo.ondraw = function (obj)
            {
                for (var i=0; i<obj.coords.length; ++i) {
                    obj.context.fillStyle = color_texto;
                    RGraph.Text2(obj.context, {
                                               /*font:tipo_letra,
                                               'size':tamano_letra,*/
                                               'x':obj.coords[i][0] + (obj.coords[i][2] / 2),
                                               'y':obj.coords[i][1] + (obj.coords[i][3] / 2),
                                               'text':numeral(obj.data_arr[i]).format('0,0'),
                                               'valign':'center',
                                               'halign':'center'
                                              });
                }
            };
        bar_costo.Draw();
}

/*
Construye los graficos de resumen comparativo asociados al elemento escogido por
el usuario.
*/
function busquedaResumenComp(data){
	console.log(data);
  for(x=0; x<data.estadisticas.contribucion.rows.length; x++){
      if ( data.estadisticas.contribucion.rows[x][0] < 0 )
          data.estadisticas.contribucion.rows[x][0] = 0;
      if ( data.estadisticas.costo.rows[x] < 0 )
          data.estadisticas.costo.rows[x] = [0];
      for(k=0; k<data.estadisticas.dcto_precio.rows[x].length; k++){
          if ( data.estadisticas.dcto_precio.rows[x][k] < 0 )
              data.estadisticas.dcto_precio.rows[x][k] = [0];
      }
  }
    var data_unidades = data.estadisticas.unidades;
    var data_venta = data.estadisticas.venta;
    var data_contribucion = data.estadisticas.contribucion;
    var data_margen = data.estadisticas.margen;
    var data_costo = data.estadisticas.costo;
    var data_dcto_precio = data.estadisticas.dcto_precio;

    var colores_arr = ['#44bbcc','#88dddd','#bbeeff'];
    var color_linea_margen = ['#0055bb'];
    var color_texto = 'black';
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
        .Set('background.grid', false);
    bar_venta.ondraw = function (obj)
        {
            for (var i=0; i<obj.coords.length; ++i) {
                obj.context.fillStyle = color_texto;
                if ( data_venta.ingraph[i] != null ) {
                    RGraph.Text2(obj.context, {
                       //font:tipo_letra,
                       //'size':tamano_letra,
                       'x':obj.coords[i][0] + (obj.coords[i][2] / 2),
                       'y':obj.coords[i][1] + (obj.coords[i][3] / 2),
                       'text':data_venta.ingraph[i][0],
                       'valign':'center',
                       'halign':'center'
                    });    
                }
            }
        };
    bar_venta.Draw();

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
        .Set('background.grid', false);
    bar_unidades.ondraw = function (obj)
        {
            for (var i=0; i<obj.coords.length; ++i) {
                obj.context.fillStyle = color_texto;
                if ( data_unidades.ingraph[i] != null ) {
                    RGraph.Text2(obj.context, {
                       //font:tipo_letra,
                       //'size':tamano_letra,
                       'x':obj.coords[i][0] + (obj.coords[i][2] / 2),
                       'y':obj.coords[i][1] + (obj.coords[i][3] / 2),
                       'text':data_unidades.ingraph[i][0],
                       'valign':'center',
                       'halign':'center'
                    });    
                }
            }
        };
    bar_unidades.Draw();

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
        .Set('background.grid', false);
    bar_contribucion.ondraw = function (obj) {
        for (var i=0; i<obj.coords.length; ++i) {
            obj.context.fillStyle = color_texto;
            if ( data_contribucion.ingraph[i] != null ) {
                RGraph.Text2(obj.context, {
                   //font:tipo_letra,
                   //'size':tamano_letra,
                   'x':obj.coords[i][0] + (obj.coords[i][2] / 2),
                   'y':obj.coords[i][1] + (obj.coords[i][3] / 2),
                   'text':data_contribucion.ingraph[i][0],
                   'valign':'center',
                   'halign':'center'
                });    
            }
        }
    };

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
		.Set('outofbounds', true);
    line_margen.ondraw = function (obj) {
        for (var i=0; i<obj.coords.length; ++i) {
            obj.context.fillStyle = color_texto;
            if ( data_margen.ingraph[i] != null ) {
                RGraph.Text2(obj.context, {
                   //font:tipo_letra,
                   //'size':tamano_letra,
                   'x':obj.coords[i][0],
                   'y':obj.coords[i][1] - 10,
                   'text':data_margen.ingraph[i][0],
                   'valign':'center',
                   'halign':'center'
                });    
            }
        }
    };
    var combo = new RGraph.CombinedChart(bar_contribucion, line_margen);
	combo.Draw();
    
    var bar_precio_dcto = new RGraph.Bar('precio-chart-comp', data_dcto_precio.rows)
        .Set('text.color', color_texto)
        .Set('colors', colores_arr)
        .Set('labels', data_dcto_precio.cols)
        .Set('hmargin', 20)
        .Set('grouping', 'stacked')
        .Set('noyaxis', true)
        .Set('background.grid', false)
        .Set('ylabels', false)
        .Set('linewidth', 2)
        .Set('strokestyle', 'white');
        
    bar_precio_dcto.ondraw = function (obj)
        {
            /* Se agregan los valores por el costado izquierdo de cada barra. */
            for (var j=0; j<data_dcto_precio.labels_aux.length; ++j) {
                obj.context.fillStyle = color_texto;
                for (var i=0; i<data_dcto_precio.labels_aux[j].length; ++i) {
                    RGraph.Text2(obj.context, {
                                               /*font:tipo_letra,
                                               'size':tamano_letra,*/
                                               'x':obj.coords2[j][i+1][0] + obj.coords2[j][i+1][2],
                                               'y':obj.coords2[j][i+1][1],
                                               'text':numeral(data_dcto_precio.labels_aux[j][i]).format('0,0'),
                                               'valign':'center',
                                               'halign':'left'
                                              });
                }
            }
            /* Se agregan los totales de cada barra por sobre la barra completa. */
            for (var i=0; i<obj.coords2.length; ++i) {
                obj.context.fillStyle = color_texto;
                RGraph.Text2(obj.context, {
                                           /*font:tipo_letra,
                                           'size':tamano_letra,*/
                                           'x':obj.coords2[i][0][0] + (obj.coords2[i][0][2] / 2),
                                           'y':obj.coords2[i][0][1] - 7,
                                           'text':numeral(data_dcto_precio.labels[i]).format('0,0'),
                                           'valign':'center',
                                           'halign':'center'
                                          });
            }
        };
    bar_precio_dcto.Draw();
    
    var bar_costo = new RGraph.Bar('precio-chart-comp', data_costo.rows)
        .Set('text.color', color_texto)
        .Set('ymax', bar_precio_dcto.scale2.max)
        .Set('colors', color_linea_margen)
        .Set('noaxes', true)
        .Set('hmargin', 32)
        .Set('ylabels', false)
        .Set('noyaxis', true)
        .Set('background.grid', false);
    bar_costo.ondraw = function (obj)
        {
            for (var i=0; i<obj.coords.length; ++i) {
                obj.context.fillStyle = color_texto;
                RGraph.Text2(obj.context, {
                                           /*font:tipo_letra,
                                           'size':tamano_letra,*/
                                           'x':obj.coords[i][0] + (obj.coords[i][2] / 2),
                                           'y':obj.coords[i][1] + (obj.coords[i][3] / 2),
                                           'text':numeral(obj.data_arr[i]).format('0,0'),
                                           'valign':'center',
                                           'halign':'center'
                                          });
            }
        };
    bar_costo.Draw();
}