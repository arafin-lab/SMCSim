#ifndef PARAMS_H
#define PARAMS_H

// The seed of the random generator
#define RANDOM_SEED 0

// General Graph Parameter
/****************************************************************************/

// Number of node in the random graph
#define NODES 100      

// Number of components (subgraphs) in the grap
#define NUM_COMPONENTS 4

// Maximum outdegree of each node in the random graph (component connectivity)
#define MAX_COMPONENT_OUTDEGREE 10

// Kernel specific parameters
/****************************************************************************/

// Bellman Ford
#define MAX_WEIGHT 10

// BFS
#define BFS_MAX_ITERATIONS 10

// Pagerank
#define PAGERANK_MAX_ITERATIONS 100
#define PAGERANK_MAX_ERROR 0.001

#endif
