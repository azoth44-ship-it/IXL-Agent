import pytest
from ixl_agent.probability import solve_distribution
@pytest.mark.parametrize('values,answer', [(['0.2','0.1','0.2','0.6'],'no'),(['0.1','0.2','0.7'],'yes'),(['-0.1','0.5','0.6'],'no'),(['1.1','-0.1'],'no'),(['1/3','2/3'],'yes'),(['0','1'],'yes'),(['0.2','0.3'],'no')])
def test_distribution(values,answer):
 data={'instruction':'Does the table show the values of a valid probability function on the outcomes in a sample space?','headers':['Probability'],'rows':[[v] for v in values]}
 assert solve_distribution(data)['answer']==answer
