typedef unsigned int size_t;
/*@ ghost extern int __fc_heap_status __attribute__((__FRAMA_C_MODEL__)); */

/*@
axiomatic dynamic_allocation {
  predicate is_allocable{L}(size_t n) 
    reads __fc_heap_status;
  
  }
 */
void sort(void)
{
  return;
}


