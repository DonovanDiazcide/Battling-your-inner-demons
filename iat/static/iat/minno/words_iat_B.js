define(['pipAPI','https://cdn.jsdelivr.net/gh/baranan/minno-tasks@0.7.3/IAT/qualtrics/quiat9.js'],
function(APIConstructor, iatExtension){
    var API = new APIConstructor();

    return iatExtension({
        category1 : {
            name : 'Categoría X',
            title : {
                media : {word : 'Categoría X'},
                css : {color:'#31940F','font-size':'2em'},
                height : 4
            },
            stimulusMedia : [
                {word:'roble'},
                {word:'pino'},
                {word:'cedro'},
                {word:'abeto'},
                {word:'olmo'},
                {word:'haya'}
            ],
            stimulusCss : {color:'#31940F','font-size':'1.8em'}
        },
        category2 : {
            name : 'Categoría Y',
            title : {
                media : {word : 'Categoría Y'},
                css : {color:'#31940F','font-size':'2em'},
                height : 4
            },
            stimulusMedia : [
                {word:'lago'},
                {word:'río'},
                {word:'mar'},
                {word:'océano'},
                {word:'bahía'},
                {word:'estero'}
            ],
            stimulusCss : {color:'#31940F','font-size':'1.8em'}
        }
    });
});
