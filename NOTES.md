# Questions autour des edges cases

## Dates de disponibilité des produits saisonniers

- Comportement actuel : les dates de début et de fin sont exclues.
- Question : le produit est-il vendable ces deux jours ?

## Date d'expiration

- Comportement actuel : un produit qui expire aujourd'hui est indisponible.
- Question : peut-il être vendu pendant toute sa date d'expiration ?

## Produit saisonnier avec stock

- Comportement actuel : dans certains cas, le délai peut entraîner
  une mise à zéro du stock alors que des unités sont disponibles.
- Question : faut-il appliquer la règle de réapprovisionnement
  uniquement lorsque le stock est épuisé ?