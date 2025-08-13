define(['pipAPI','https://cdn.jsdelivr.net/gh/baranan/minno-tasks@0.7.3/IAT/qualtrics/quiat9.js'],
function(APIConstructor, iatExtension){
    var API = new APIConstructor();

    return iatExtension({
        category1 : {
            name : 'Grupo A',
            title : {
                media : {word : 'Letras griegas'},
                css : {color:'#31940F','font-size':'2em'},
                height : 4
            },
            stimulusMedia : [
                {word:'alfa'},
                {word:'beta'},
                {word:'gamma'},
                {word:'delta'},
                {word:'epsilon'},
                {word:'zeta'}
            ],
            stimulusCss : {color:'#31940F','font-size':'1.8em'}
        },
        category2 : {
            name : 'Grupo B',
            title : {
                media : {word : 'Numeros'},
                css : {color:'#31940F','font-size':'2em'},
                height : 4
            },
            stimulusMedia : [
                {word:'uno'},
                {word:'dos'},
                {word:'tres'},
                {word:'cuatro'},
                {word:'cinco'},
                {word:'seis'}
            ],
            stimulusCss : {color:'#31940F','font-size':'1.8em'}
        }
        // (usamos los atributos por defecto del extension, igual que el ejemplo)
    });
});
