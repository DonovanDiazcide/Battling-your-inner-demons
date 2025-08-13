define(['pipAPI', 'https://cdn.jsdelivr.net/gh/baranan/minno-tasks@0.*/stiat/qualtrics/qstiat6.js'],
function(APIConstructor, stiatExtension){
  var API = new APIConstructor();
  return stiatExtension({
    category : {
      name  : 'People with disabilities',
      title : { media:{word:'People with disabilities'}, css:{color:'#31b404','font-size':'2em'}, height:7 },
      media : [
        {word:'wheelchair user'},{word:'blind person'},{word:'deaf person'},
        {word:'person with autism'},{word:'amputee'},{word:'chronic illness'}
      ],
      css   : {color:'#31b404','font-size':'3em'}
    },
    attribute1 : {
      name:'Unpleasant',
      title:{ media:{word:'Negative'}, css:{color:'#31b404','font-size':'2em'}, height:7 },
      media:[
        {word:'Bomb'},{word:'Abuse'},{word:'Sadness'},{word:'Pain'},{word:'Poison'},{word:'Grief'}
      ],
      css:{color:'#31b404','font-size':'3em'}
    },
    attribute2 : {
      name:'Pleasant',
      title:{ media:{word:'Positive'}, css:{color:'#31b404','font-size':'2em'}, height:7 },
      media:[
        {word:'Paradise'},{word:'Pleasure'},{word:'Cheer'},{word:'Wonderful'},{word:'Splendid'},{word:'Love'}
      ],
      css:{color:'#31b404','font-size':'3em'}
    }
  });
});
