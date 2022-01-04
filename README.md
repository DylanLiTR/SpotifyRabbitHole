## Spotify Rabbit Hole

### Inspiration
Have you ever found yourself in the YouTube rabbit hole, constantly clicking on videos recommended in the right sidebar? I sure have, whether it be memes or TedTalks, so I wanted to create something similar for songs. 

### V1 - SGDClassifier using partial_fit on mini-batches of 5
#### Strengths
- Gets new data relatively quickly as the user rates 5 at a time

#### Limitations
- Requires the user to input a song for every rating label from 1-5 at the start as SGDClassifier needs all labels
  - Many users do not keep track of songs they dislike

### V2 - River Pipeline using predict_one/learn_one on one new data point each time
#### Strengths
- Listening to one song at a time makes more sense

##### *At this point, both are only marginally better than randomly picking a rating from 1-5*

## Notes
### What I've tried
1. Binary classification and multiclass classification
2. Ranking the 5 recommendations by relative preference

### Issues I've faced and what I've learned
- Difficult to predict human preferences
- Learning parameters for a new user is slow without other users for collaborative filtering (cold start)
- More data is not necessarily better (data imbalance)
  - There is generally an imbalance of data between classes as people generally dislike more songs than they like, or are neutral about a significant proportion of songs
- Scikit Learn Pipeline unable to use partial_fit for incremental learning
  - Feature scaling will be done using StandardScaler fit on a large dataset
- River is a new library for online/incremental machine learning and has limited documentation

### Things to fix
1. Error when submitting without checking a radio button (use JS preventdefault)
2. Find a better way to retrieve songs instead of getting a large set of recommendations from Spotify (could take a large dataset and use K Nearest Neighbours to find similar songs)
   - It's ironic that this program sorts through Spotify's recommendations to give recommendations

### Things to try
- Bayesian Personalized Ranking
- Oversampling minority classes to counteract imbalanced classes
- Sort by predict_proba
- Instead of using partial_fit on new data, using fit on all data with a new model every time
  - Feasible on small datasets such as those used in this program but unable to scale
- Styling with CSS and deploying with Heroku

### Any advice would be appreciated!
