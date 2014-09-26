/*
    Realiza un conteo de los nodos a planificar
*/
function definirVisibles(){
    var html = "";
    var nodos_planificables = 0;
    var nodos_visibles = 0;
    $("#treetable").fancytree("getTree").visit(function(node){
        if(!(typeof node.extraClasses == "undefined") && (node.extraClasses == "planificable")){
            if (node.isVisible()){
                if (node.hasChildren()){
                    if (!node.isExpanded()){
                        nodos_planificables++;
                    }
                }
                else{
                    nodos_planificables++;
                }
                
            }
        }
        if (node.isVisible()){
            nodos_visibles++;
        }
        
    });
    html += "<p>Items Totales: " + nodos_visibles + " | Items a Planificar: " + nodos_planificables + "</p>";
    $("#msg_visibles").html(html);
    return false;
}

/*
    Abre un dialog que permite generar un registro de agrupacion de item (Grupoitem). 
    Esto implica la creacion de un nuevo Item y un registro de Grupoitem por cada 
    Item que se agrupo.
*/
function crearGrupoitem(){
    var agrupacion_valida = true;
    var num_items = 0;        
    var items_arr = [],
        items_arr_keys = [];
    var tree;
    tree = $("#treetable").fancytree("getTree");
    // Se genera obtiene un arreglo con los nodos seleccionados por el usuario
    items_arr = tree.getSelectedNodes();
    // Se almacena la cantidad de items que han sido seleccionados por el usuario
    num_items = items_arr.length;
    
    // Validaciones antes de permitir guardar la agrupacion
    // Se verifica que el usuario haya seleccionado al menos dos items para crear una agrupacion
    if ( num_items <= 1 ){
        agrupacion_valida = false;
        msg = "Una agrupación debe contener al menos 2 items.";
        tipo = "msg_warning";
        mostrarMensaje(msg, tipo);
        return false;
    }
    else{
        // Se valida que todos los items pertenezcan al mismo padre. Es decir, no se pueden
        // agrupar items de distintas ramas (padres)
        for (var x=1; x<num_items; x++){
            if ( items_arr[x].parent != items_arr[x-1].parent ){
                agrupacion_valida = false;
                break;
            }
        }
        if ( !agrupacion_valida ){
            msg = "No es posible agrupar items que pertenezcan a distintas ramas (padres).";
            tipo = "msg_warning";
            mostrarMensaje(msg, tipo);
            return false;
        }
    }
    // Se despliega el dialog con el formulario a completar (informacion del nuevo item a crear)
    for(var x = 0; x<num_items; x++){
        items_arr_keys.push(items_arr[x].key);
    }
    items_arr[0].title

    $("#grupo_items").val(items_arr_keys);
    $( "#dialog-form" ).dialog( "open" );
}

/*
    Se encarga de validar que los parametros de creacion de un Grupoitem cumplan con los
    requisitos minimos. En caso afirmativo, genera una peticion AJAX para que este nuevo
    Grupoitem sea guardado.
*/
function guardarGrupoItem(){
    var nombre = $( "#nombre-grupoitem" ),
        grupo_items = $( "#grupo_items" ),
        allFields = $( [] ).add( nombre );
    var bValid = true;
    allFields.removeClass( "ui-state-error" );

    bValid = bValid && checkLength( nombre, "nombre", 5, 70 );
    bValid = bValid && checkRegexp( nombre, /^[a-zA-ZñÑ]*/, "El nombre debe comenzar con una letra (a-z)." );

    // Si todas las validaciones resultaron positivas se gatilla la solicitud AJAX que crea el nuevo item,
    // grupoitem, quita la vigencia de los antiguos items y crea los nuevos registros de venta asociados
    // al nuevo item
    if ( bValid ) {
        var tree = $("#treetable").fancytree("getTree");
        nombre.val("(GRUPO) " + nombre.val());
        $.ajax({
            data: $("#crear_grupoitem_form").serialize(),
            url: '/categorias/grupoitem/create/',
            type: 'post',
            success: function(data){
                var nodo_padre = tree.getNodeByKey(String(data.item_padre_id));
                nodo_padre.load(true);
                mostrarMensaje(data.msg, "msg_success");
            }
        });
        $( this ).dialog( "close" );
    }
}

/*
    Envia una peticion Ajax con el ID del item que se desea quitar
    del arbol de planificacion. Es implica setear el campo vigencia
    en False.
*/

// DEPRECADA
function quitarVigenciaItem(){
    var nodo = $(this).data('node');
    $( "#item_id" ).val(nodo.key);
    $.ajax({
        data: $("#quitar_vigencia_item_form").serialize(),
        url: '/categorias/item/quitar-vigencia/',
        type: 'post',
        success: function(data){
            var tree = $("#treetable").fancytree("getTree");
            nodo.remove();
            mostrarMensaje(data.msg, data.tipo_msg);
            definirVisibles();
        }
    });
    $( this ).dialog( "close" );
}

/*
    Se encarga de validar que los parametros de creacion de un Item cumplan con los
    requisitos minimos. En caso afirmativo, genera una peticion AJAX para que este nuevo
    Item sea guardado.
*/
function guardarNuevoItem(){
    var nombre = $( "#nombre-item" ),
        precio = $( "#precio-item" ),
        allFields = $( [] ).add( nombre ).add( precio );
    var bValid = true;
    allFields.removeClass( "ui-state-error" );
    bValid = bValid && checkLength( nombre, "nombre", 5, 70 );
    bValid = bValid && checkLength( precio, "precio", 1, 10 );
    bValid = bValid && checkRegexp( nombre, /^[a-zA-ZñÑ]*/, "El nombre debe comenzar con una letra (a-z)." );
    bValid = bValid && checkRegexp( precio, /^\d+$/, "El precio solo admite números enteros (0-9)." );

    // Si todas las validaciones resultaron positivas se gatilla la solicitud AJAX que crea el nuevo item,
    if ( bValid ) {
        var nodo = $(this).data('node');
        $( "#item_padre_id" ).val(nodo.key);
        $.ajax({
            data: $("#crear_item_form").serialize(),
            url: '/categorias/item/create-ajax/',
            type: 'post',
            success: function(data){
                var tree = $("#treetable").fancytree("getTree");
                var nodo_padre = tree.getNodeByKey(String(data.id_item_padre));
                nodo_padre.load(true);
                mostrarMensaje(data.msg, "msg_success");
            }
        });
        $( this ).dialog( "close" );
        var nombre = $( "#nombre-item" ),
            precio = $( "#precio-item" ),
            allFields = $( [] ).add( nombre ).add( precio );
        allFields.val( "" ).removeClass( "ui-state-error" );
        $( ".validateTips" ).html("Todos los campos son requeridos.");
    }
}
/*
    
*/
function updateTips( t ) {
    arbol_obj.getTips()
    .text( t )
    .addClass( "ui-state-highlight" );
    setTimeout(function() {
        arbol_obj.getTips().removeClass( "ui-state-highlight", 1500 );
    }, 500 );
}

/*
    
*/
function checkLength( o, n, min, max ) {
    if ( o.val().length > max || o.val().length < min ) {
        o.addClass( "ui-state-error" );
        updateTips( "El largo del campo " + n + " debe contener entre " +
        min + " y " + max + " letras." );
        return false;
    } else {
        return true;
    }
}

/*
    
*/
function checkRegexp( o, regexp, n ) {
    if ( !( regexp.test( o.val() ) ) ) {
        o.addClass( "ui-state-error" );
        updateTips( n );
        return false;
    } else {
        return true;
    }
}

/*
    Se encarga de desplegar el div superior con un mensaje y estilo
    pasado como parametro.
*/
function mostrarMensaje(msg, tipo){
    $("#caja-mensajes")
        .show()
        .html(msg)
        .addClass(tipo)
        .delay(3000)
        .queue(function(next){ 
            $(this).hide();
            $(this).removeClass(tipo);
            $(this).html("");
            next(); 
        });
}
