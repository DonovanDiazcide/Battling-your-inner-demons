define(['pipAPI', 'https://cdn.jsdelivr.net/gh/baranan/minno-tasks@0.*/IAT/qualtrics/qiat9.js'],
function(APIConstructor, iatExtension){
  var API = new APIConstructor();
  return iatExtension({
    // ================== TUS DOS CATEGORÍAS (Targets) ==================
    category1: { // Target A
      name: 'Flowers',
      title: { media:{word:'Flowers'}, css:{color:'#31b404','font-size':'2em'}, height:7 },
      media: [
        {word:'Orchid'},{word:'Rose'},{word:'Lily'},{word:'Daisy'},{word:'Tulip'},{word:'Violet'}
      ],
      css: {color:'#31b404','font-size':'3em'}
    },
    category2: { // Target B
      name: 'Insects',
      title: { media:{word:'Insects'}, css:{color:'#31b404','font-size':'2em'}, height:7 },
      media: [
        {word:'Cockroach'},{word:'Mosquito'},{word:'Wasp'},{word:'Fly'},{word:'Gnat'},{word:'Locust'}
      ],
      css: {color:'#31b404','font-size':'3em'}
    },

    // ================== ATRIBUTOS (Positive / Negative) ==================
    attribute1: {
      name:'Unpleasant',
      title:{ media:{word:'Negative'}, css:{color:'#31b404','font-size':'2em'}, height:7 },
      media:[
        {word:'Bomb'},{word:'Abuse'},{word:'Sadness'},{word:'Pain'},{word:'Poison'},{word:'Grief'}
      ],
      css:{color:'#31b404','font-size':'3em'}
    },
    attribute2: {
      name:'Pleasant',
      title:{ media:{word:'Positive'}, css:{color:'#31b404','font-size':'2em'}, height:7 },
      media:[
        {word:'Paradise'},{word:'Pleasure'},{word:'Cheer'},{word:'Wonderful'},{word:'Splendid'},{word:'Love'}
      ],
      css:{color:'#31b404','font-size':'3em'}
    },

    // base_url : { image : 'https://TU-SERVIDOR/imagenes/' } // solo si usas imágenes

    // (Mantenemos la configuración por defecto de qiat9: 7 bloques, etc.)
  });
});
