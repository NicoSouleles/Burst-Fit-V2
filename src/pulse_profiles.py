import numpy as np


def rightleft(x : np.ndarray, amp : float, b : float, c1 : float, 
              lam : float, d1 : float, d2 : float) -> np.ndarray:
    """
    Original pulse shape function taken directly from Anna Hwang's code in 2019, 
    after the work she did on finding the pulse shape produced by the 
    photodiode.

    Consists of a gaussian function with an exponential tail.
    
    None of the parameters for this function are fitting parameters, they are 
    all set to optimal values determined by Anna for the shape of the pulse, 
    which are loaded using "load_pulse_params"
    """
    delta_t = 200e-12

    # Defines which part of the function is defined where.
    step_function = np.heaviside(x - b - delta_t, amp / 2)

    h1 = amp-d1
    h2 = h1 * np.exp(-delta_t**2 / (2 * c1**2)) + d1 - d2

    gaussian = h1 * np.exp(-(x - b)**2 / (2 * c1**2)) + d1
    exp_tail = h2 * np.exp(-lam * (x - b - delta_t)) + d2

    return gaussian * (1 - step_function) + exp_tail * step_function


class PulseShape:
    """
    Abstract class representing a pulse shape object.
    """

    def __init__(self) -> None:
        self.parameters = None
        self.param_num = None

    def set_params(self, new_params):
        
        if len(new_params) != self.param_num:
            raise ValueError(f"Must set {self.param_num} number of parameters"
                             "for this pulse shape function.")
        
        self.parameters = new_params

    def pulse_shape(self, t : np.ndarray, *params):
        raise NotImplementedError
    
    def norm_pulse_shape(self, t : np.ndarray, *params):
        return self.pulse_shape(t, *params) / self.pulse_shape(0, *params)


class GaussianExp(PulseShape):
    """
    Inherits from PulseShape. This pusle shape represents a gaussian
    curve with an exponential tail. Modified version from Anna Hwang's
    initial pulse shape.
    """

    def __init__(self, filepath) -> None:
        super().__init__()
        
        self.parameters = np.loadtxt(filepath, skiprows = 1)
        self.param_num = self.parameters.size
        self.param_bounds = ([1e-11, 0], [1e-9, 1e9])

        # Pre-calculates values related to the pulse shape parameters. Only
        # use if the parameters to be used are going to be kept constant
        # for the lifetime of the class.
        self.make_performant = False

        sigma_val, lambda_val = self.parameters
        # Differentiability condition
        self.delta_t = lambda_val * sigma_val**2 
        # Continuity condition
        self.h2 = np.exp(-self.delta_t**2 / (2 * sigma_val**2)) 

    def pulse_shape(self, t : np.ndarray, *params) -> np.ndarray:        
        """
        MODIFIED pulse shape function taken from Anna Hwang's code in 2019, after 
        the work she did on finding the pulse shape produced by the photodiode.

        Consists of a gaussian function with an exponential tail.
        
        None of the parameters for this function are fitting parameters, they are 
        all set to optimal values determined by Anna for the shape of the pulse, 
        which are loaded form an external file.
        """
        if self.make_performant:
            sig, lam = self.parameters
            delta_t = self.delta_t
            h2 = self.h2
        else:
            sig, lam = params
            # Differentiability condition
            delta_t = lam * sig**2 
            # Continuity condition
            h2 = np.exp(-delta_t**2 / (2 * sig**2)) 

        step_function = np.heaviside(t - delta_t, h2)

        gaussian = np.exp(-t**2 / (2 * sig**2))
        exp_tail = h2 * np.exp(-lam * (t - delta_t))

        # Optionally disable output validation check to save time.
        if not self.make_performant:
            if not np.all(np.isfinite(exp_tail)):
                raise ValueError("Exponential overflow; input value is too "
                                "extreme.")
 
        return gaussian * (1 - step_function) + exp_tail * step_function

    def norm_pulse_shape(self, t: np.ndarray, *params):
        """
        Override this function, since a guassian does not need to be 
        normalized.
        """
        return self.pulse_shape(t, *params)


class Lorentzian(PulseShape):

    def __init__(self) -> None:
        super().__init__()

        GAMMA = 4e-10
        LAMBDA = 500000000
        self.parameters = GAMMA, LAMBDA

    def pulse_shape(self, t : np.ndarray, *params) -> np.ndarray:
        """
        Similar to the gaussian pulse with an exponential tail 
        `modified_gaussian_exp`, but the pulse has a lorenzian shape, while the 
        tail is still exponential. 
        """
        gamma, lam = params
        
        if 1 < (gamma * lam)**2:
            raise ValueError("Invalid parameter input.")

        # Differentiability condition   
        delta_t = 1 / lam + np.sqrt(1 / (lam**2) - gamma**2)
        # Continuity condition
        h2 = 1 / (np.pi * gamma * (1 + (delta_t / gamma)**2))
        # Defines which part of the function is defined where.
        step_function  = np.heaviside(t - delta_t, h2) 

        lorenzian = 1 / (np.pi * gamma * (1 + (t / gamma)**2))
        exp_tail = h2 * np.exp(-lam * (t - delta_t))

        return lorenzian * (1 - step_function) + exp_tail * step_function


class Logistic(PulseShape):

    def __init__(self) -> None:
        super().__init__()

        self.parameters = None
        raise NotImplementedError

    def pulse_shape(self, t : np.ndarray, *params):
        
        s = params
        return 1 / np.cosh(t / (2 * s))**2

class LogNormal(PulseShape):

    def __init__(self) -> None:
        super().__init__()

        self.parameters = None
        raise NotImplementedError
    
    def pulse_shape(self, t : np.ndarray, *params):
        
        a, b = params
        
        if type(t) is not np.ndarray:
            t = np.array(t)
        
        start_point = -1 / a    
        valid_time_idxs = np.vectorize(lambda x : start_point < x)(t)
        valid_t = t[valid_time_idxs]

        log_normal = np.zeros(shape=t.shape)
        log_normal[valid_time_idxs] = np.exp(-np.log(a * valid_t + 1)**2 / \
                                            (2 * b**2))
        return log_normal
