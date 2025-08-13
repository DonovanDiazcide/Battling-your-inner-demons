// iat_two_cat_local.js — 100% local
define(['pipAPI', '/static/minno/minno-tasks/IAT/qualtrics/quiat9.js'], function(APIConstructor, iatExtension){
    var API = new APIConstructor();

    // IAT con dos categorías (palabras) y atributos buenos/malos
    return iatExtension({
        fullscreen: false,
        isTouch: false,

        // Categorías (ejemplo neutro)
        category1 : {
            name  : 'Flores',
            title : { media:{word:'Flores'}, css:{color:'#336600','font-size':'1.8em'}, height:4 },
            stimulusMedia : [
                {word:'margarita'},{word:'rosa'},{word:'lirio'},
                {word:'tulipán'},{word:'orquídea'},{word:'dalia'}
            ],
            stimulusCss : {color:'#336600','font-size':'2.3em'}
        },
        category2 : {
            name  : 'Insectos',
            title : { media:{word:'Insectos'}, css:{color:'#336600','font-size':'1.8em'}, height:4 },
            stimulusMedia : [
                {word:'mosca'},{word:'hormiga'},{word:'cucaracha'},
                {word:'abeja'},{word:'mosquito'},{word:'avispón'}
            ],
            stimulusCss : {color:'#336600','font-size':'2.3em'}
        },

        // Atributos
        attribute1 : {
            name  : 'Malas',
            title : { media:{word:'Malas'}, css:{color:'#0000FF','font-size':'1.8em'}, height:4 },
            stimulusMedia : [
                {word:'horrible'},{word:'terrible'},{word:'asqueroso'},{word:'triste'},
                {word:'nausea'},{word:'dolor'},{word:'desastre'},{word:'fracaso'}
            ],
            stimulusCss : {color:'#0000FF','font-size':'2.3em'}
        },
        attribute2 : {
            name  : 'Buenas',
            title : { media:{word:'Buenas'}, css:{color:'#0000FF','font-size':'1.8em'}, height:4 },
            stimulusMedia : [
                {word:'feliz'},{word:'alegría'},{word:'placer'},{word:'sonrisa'},
                {word:'maravilla'},{word:'amor'},{word:'paz'},{word:'gloria'}
            ],
            stimulusCss : {color:'#0000FF','font-size':'2.3em'}
        },

        // No usamos imágenes → no necesitamos base_url.image
        // Si en algún momento agregas imágenes, define:
        // base_url: { image: '/static/minno/images/' },

        // Tamaños y bloques (valores típicos)
        canvas : { maxWidth: 725, proportions: 0.7, background:'#fff', canvasBackground:'#fff', borderColor:'lightblue', borderWidth:5 },
        blockAttributes_nTrials    : 20,
        blockAttributes_nMiniBlocks: 5,
        blockCategories_nTrials    : 20,
        blockCategories_nMiniBlocks: 5,
        blockFirstCombined_nTrials : 20,
        blockFirstCombined_nMiniBlocks: 5,
        blockSecondCombined_nTrials: 40, // pon 0 si quieres IAT de 5 bloques
        blockSecondCombined_nMiniBlocks: 10,
        blockSwitch_nTrials        : 28,
        blockSwitch_nMiniBlocks    : 7,

        randomAttSide  : false, // atributo2 a la derecha
        randomBlockOrder: true,  // aleatoriza qué categoría va primero a la derecha

        // Mensajes/instrucciones por defecto (dejamos los del script)
        showDebriefing: false
    });
});
