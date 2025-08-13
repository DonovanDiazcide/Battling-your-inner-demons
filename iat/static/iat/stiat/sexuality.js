define(['pipAPI','https://cdn.jsdelivr.net/gh/baranan/minno-tasks@0.*/stiat/qualtrics/qstiat6.js'],
function(APIConstructor, stiatExtension){
  var API = new APIConstructor();
  return stiatExtension({
    category : {
      name  : 'Gay people',
      title : { media:{word:'Gay people'}, css:{color:'#31b404','font-size':'2em'}, height:7 },
      media : [
        {word:'gay men'},{word:'lesbian women'},{word:'same-sex couples'},
        {word:'homosexual'},{word:'LGBTQ+'},{word:' LGBTQIA+'}
      ],
      css   : {color:'#31b404','font-size':'3em'}
    },
    attribute1 : {
      name:'Unpleasant',
      title:{ media:{word:'Negative'}, css:{color:'#31b404','font-size':'2em'}, height:7 },
      media:[{word:'Bomb'},{word:'Abuse'},{word:'Sadness'},{word:'Pain'},{word:'Poison'},{word:'Grief'}],
      css:{color:'#31b404','font-size':'3em'}
    },
    attribute2 : {
      name:'Pleasant',
      title:{ media:{word:'Positive'}, css:{color:'#31b404','font-size':'2em'}, height:7 },
      media:[{word:'Paradise'},{word:'Pleasure'},{word:'Cheer'},{word:'Wonderful'},{word:'Splendid'},{word:'Love'}],
      css:{color:'#31b404','font-size':'3em'}
    }
    // base_url : { image : '...' } // sólo si usas imágenes
  });
});
