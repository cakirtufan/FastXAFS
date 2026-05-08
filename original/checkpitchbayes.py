# -*- coding: utf-8 -*-
"""
Created on Mon Mar 10 21:36:13 2025

@author: mradtke
"""

import motorlist as ml
import detectorlist as dl
from time import sleep
import numpy as np
import epics
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# Function to measure intensity at a given pitch position
def measure_intensity(pos):
    """
    Measure the intensity at a given pitch position
    
    Args:
        pos: Pitch position to measure
    
    Returns:
        Measured intensity value
    """
    ml.DCM_PIEZO.move(pos, wait=True)
    sleep(0.2)
    intensity1 = dl.ioni13.get('.VAL')
    dl.ioni13.put('rawData.SCAN', 1)
    dl.ioni13.put('rawData.PROC', 1)
    
    sleep(0.3)
    while(float(epics.caget('K6485:miocb0113rawData.PACT')) > 0):
        sleep(0.1)
    
    intensity = dl.ioni13.get('.VAL')
    if intensity==intensity1:measure_intensity(pos)
    return intensity

# Physics-informed Maximum Likelihood Estimation for peak center
def peak_center_mle(x_observed, y_observed, robustness=0.9):
    """
    Calculate the Maximum Likelihood Estimate for the peak center
    using the physics-informed weighted average formula
    
    Args:
        x_observed: Array of x coordinates (pitch positions)
        y_observed: Array of function values (intensities)
        robustness: Robustness parameter (0-1) for handling noise
    
    Returns:
        Estimated peak center
    """
    if np.sum(y_observed) > 0:
        # Basic MLE formula - weighted average with y values as weights
        mu_estimate = np.sum(x_observed * y_observed) / np.sum(y_observed)
        
        # For high noise scenarios, apply robustness adjustment
        if robustness < 1.0:
            # Find maximum y value
            max_y = np.max(y_observed)
            max_idx = np.argmax(y_observed)
            max_x = x_observed[max_idx]
            
            # Calculate weighted average between MLE and max point
            mu_estimate = robustness * mu_estimate + (1 - robustness) * max_x
            
        return mu_estimate
    else:
        # If all observations are zero, return the middle of observed x values
        return np.mean(x_observed)

# Function to estimate noise level from observed data
def estimate_noise_level(x_observed, y_observed, mu_estimate):
    """
    Estimate the noise level from observed data points
    
    Args:
        x_observed: Array of x coordinates (pitch positions)
        y_observed: Array of function values (intensities)
        mu_estimate: Current estimate of the peak center
    
    Returns:
        Estimated noise level (standard deviation)
    """
    if len(x_observed) < 5:
        return 0.5  # Default value for insufficient data
    
    # Fit a Gaussian to the data to estimate the width
    try:
        # Define Gaussian function for fitting
        def gaussian(x, mu, sigma, amplitude):
            return amplitude * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
        
        # Define error function for optimization
        def error_func(params):
            mu, sigma, amplitude = params
            predicted = gaussian(x_observed, mu, sigma, amplitude)
            return np.sum((predicted - y_observed) ** 2)
        
        # Initial guess based on data
        max_y = np.max(y_observed)
        max_idx = np.argmax(y_observed)
        max_x = x_observed[max_idx]
        
        # Rough estimate of sigma based on data spread
        sigma_guess = np.std(x_observed) / 2
        
        # Optimize to find the best fit
        result = minimize(
            error_func, 
            [mu_estimate, sigma_guess, max_y],
            bounds=[(mu_estimate - 0.1, mu_estimate + 0.1), 
                    (0.0001, 0.1), 
                    (0.1 * max_y, 2 * max_y)]
        )
        
        _, sigma, _ = result.x
        
        # Calculate residuals
        predicted = gaussian(x_observed, mu_estimate, sigma, max_y)
        residuals = y_observed - predicted
        
        # Estimate noise as standard deviation of residuals
        noise_estimate = np.std(residuals)
        
        return max(0.01, min(1.0, noise_estimate / max_y))
    
    except:
        # Fallback if fitting fails
        return 0.5

# Latin Hypercube Sampling for initial points
def latin_hypercube_sampling(n, bounds):
    """
    Generate initial points using Latin Hypercube Sampling
    
    Args:
        n: Number of samples to generate
        bounds: Tuple of (min, max) bounds for x
    
    Returns:
        Array of x coordinates
    """
    # Create n evenly spaced segments
    points = np.zeros(n)
    segment_width = (bounds[1] - bounds[0]) / n
    
    for i in range(n):
        # Sample randomly within each segment
        segment_min = bounds[0] + i * segment_width
        points[i] = segment_min + np.random.random() * segment_width
    
    # Shuffle the points to break correlation
    np.random.shuffle(points)
    
    return points

# Function to propose the next sample point
def propose_next_sample(x_observed, y_observed, bounds, iteration, total_iterations, noise_level=0.5):
    """
    Propose the next point to sample using physics-informed strategy
    
    Args:
        x_observed: Array of x coordinates (pitch positions)
        y_observed: Array of function values (intensities)
        bounds: Tuple of (min, max) bounds for x
        iteration: Current iteration number
        total_iterations: Total number of iterations planned
        noise_level: Estimated noise level
    
    Returns:
        x coordinate for the next sample
    """
    # Current best estimate of the peak center
    mu_estimate = peak_center_mle(x_observed, y_observed, 0.9)
    
    # Exploration vs. exploitation balance based on iteration progress
    progress = iteration / total_iterations
    
    # Early iterations: more exploration
    if progress < 0.3:
        # Find the largest gap in the observed points
        sorted_idx = np.argsort(x_observed)
        sorted_x = x_observed[sorted_idx]
        gaps = sorted_x[1:] - sorted_x[:-1]
        
        if len(gaps) > 0:
            max_gap_idx = np.argmax(gaps)
            # Sample in the middle of the largest gap
            return sorted_x[max_gap_idx] + gaps[max_gap_idx] / 2
        else:
            # Fallback: random point within bounds
            return bounds[0] + np.random.random() * (bounds[1] - bounds[0])
    
    # Middle iterations: balanced approach
    elif progress < 0.7:
        # Calculate uncertainty in the center estimate
        uncertainty = min(1.0, 0.5 * noise_level / np.sqrt(len(x_observed)))
        
        # Sample within the uncertainty bounds, with higher probability near the center
        sampling_width = max(0.001, uncertainty * 1.5)
        return mu_estimate + np.random.normal(0, sampling_width)
    
    # Late iterations: fine-tuning (exploitation)
    else:
        # Focus sampling very close to the current best estimate
        fine_tuning_width = max(0.0005, noise_level * 0.1)
        return mu_estimate + np.random.normal(0, fine_tuning_width)

# Function to plot the state at a specific iteration
def plot_iteration_state(ax, state, iteration):
    """
    Plot the state of the optimization at a specific iteration
    
    Args:
        ax: Matplotlib axis to plot on
        state: State dictionary from history
        iteration: Iteration number
    """
    x_observed = state['x_observed']
    y_observed = state['y_observed']
    mu_est = state['mu_estimate']
    uncertainty = state['uncertainty']
    
    # Calculate confidence interval
    conf_lower = mu_est - 1.96 * uncertainty
    conf_upper = mu_est + 1.96 * uncertainty
    
    # Plot observed data points
    ax.plot(x_observed, y_observed, 'ko', label='Observations')
    
    # Highlight the current best estimate
    ax.axvline(x=mu_est, color='g', linestyle='-', label='Current Estimate')
    
    # Show confidence interval
    ax.axvspan(conf_lower, conf_upper, alpha=0.2, color='green', label='95% CI')
    
    # Add annotation for the estimate and uncertainty
    ax.annotate(f'mu = {mu_est:.4f} +/- {uncertainty:.4f}',
                xy=(mu_est, np.max(y_observed) * 1.05), 
                xytext=(mu_est, np.max(y_observed) * 1.05),
                ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.3", fc='w', ec='green', alpha=0.8))
    
    # Set plot title and labels
    ax.set_title(f'Iteration {iteration}: Pitch Optimization')
    ax.set_xlabel('Pitch Position')
    ax.set_ylabel('Intensity')
    ax.grid(True, alpha=0.3)
    ax.legend()

# Function to plot the convergence trajectory
def plot_convergence(history):
    """
    Plot the convergence of the optimization
    
    Args:
        history: List of state dictionaries
    """
    iterations = [state['iteration'] for state in history]
    estimates = [state['mu_estimate'] for state in history]
    uncertainties = [state['uncertainty'] for state in history]
    noise_estimates = [state['noise_estimate'] for state in history]
    
    # Create confidence interval bounds
    upper_bounds = [est + 1.96 * unc for est, unc in zip(estimates, uncertainties)]
    lower_bounds = [est - 1.96 * unc for est, unc in zip(estimates, uncertainties)]
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), dpi=100)
    
    # Plot estimate convergence with confidence intervals
    ax1.plot(iterations, estimates, 'g-o', label='Center Estimate')
    ax1.fill_between(iterations, lower_bounds, upper_bounds, color='g', alpha=0.2, label='95% Confidence Interval')
    
    ax1.set_title('Center Estimate Convergence with Uncertainty')
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Center Estimate (mu)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot noise estimate
    ax2.plot(iterations, noise_estimates, 'b--*', label='Estimated Noise')
    
    ax2.set_title('Noise Level Estimate')
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Noise Level')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig("pitch_optimization_convergence.png", dpi=150)
    plt.show()

# Main function for physics-informed Bayesian optimization of pitch
def physics_informed_pitch_optimization(n_iterations=15, bounds=None, plot=True,
                                        plot_iterations=[0, 5, 10, 15]):
    """
    Physics-informed Bayesian optimization to find the optimal pitch position
    
    Args:
        n_iterations: Number of iterations to run
        bounds: Tuple of (min, max) bounds for pitch. If None, will use current position ±0.01
        plot: Whether to generate plots
        plot_iterations: List of iterations to plot
    
    Returns:
        Dictionary with optimization results
    """
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Save original scan and average modes
    scanmode_old = dl.ioni13.get('rawData.SCAN')
    averagemode_old = dl.ioni13.get('averFlt')
    dl.ioni13.put('averFlt', 0)
    
    # Set bounds if not provided
    if bounds is None:
        current_pitch = ml.DCM_PIEZO.get('VAL')
        bounds = (current_pitch - 4, current_pitch + 4)
    
    print(f"Starting pitch optimization in range: [{bounds[0]:.6f}, {bounds[1]:.6f}]")
    
    # Generate initial points with Latin Hypercube Sampling
    n_initial = 30
    initial_x = latin_hypercube_sampling(n_initial, bounds)
    
    # Add a point near the middle for better coverage
    mid_point = (bounds[0] + bounds[1]) / 2
    initial_x = np.append(initial_x, mid_point + np.random.normal(0, 0.0002))
    
    # Evaluate function at initial points
    x_observed = initial_x.copy()
    y_observed = np.array([measure_intensity(x) for x in x_observed])
    
    # Store optimization history
    history = []
    
    # Initial estimate
    mu_estimate = peak_center_mle(x_observed, y_observed, 0.9)
    noise_estimate = 0.5  # Initial guess
    
    # Calculate uncertainty
    uncertainty = 0.5 * noise_estimate / np.sqrt(len(x_observed))
    
    # Store initial state
    history.append({
        'iteration': 0,
        'x_observed': x_observed.copy(),
        'y_observed': y_observed.copy(),
        'mu_estimate': mu_estimate,
        'noise_estimate': noise_estimate,
        'uncertainty': uncertainty,
        'conf_lower': mu_estimate - 1.96 * uncertainty,
        'conf_upper': mu_estimate + 1.96 * uncertainty
    })
    
    # Create figure for multiple plots if needed
    if plot and len(plot_iterations) > 0:
        n_plots = len(plot_iterations)
        fig, axs = plt.subplots(n_plots, 1, figsize=(10, 5 * n_plots), dpi=100)
        if n_plots == 1:
            axs = [axs]  # Make it indexable for single plot case
    
    # Run iterations
    for i in range(n_iterations):
        # Estimate current noise level if we have enough data
        if i >= 2:
            noise_estimate = estimate_noise_level(x_observed, y_observed, mu_estimate)
        
        # Propose next point using physics-informed strategy
        next_x = propose_next_sample(x_observed, y_observed, bounds, i, n_iterations, noise_estimate)
        
        # Evaluate function at the proposed point
        next_y = measure_intensity(next_x)
        #next_x=ml.DCM_PIEZO.get('RBV')
        # Add to observed data
        x_observed = np.append(x_observed, next_x)
        y_observed = np.append(y_observed, next_y)
        
        # Update estimate with adaptive robustness
        robustness = min(0.95, max(0.5, 1.0 - noise_estimate / 5.0))
        mu_estimate = peak_center_mle(x_observed, y_observed, robustness)
        
        # Calculate uncertainty
        uncertainty = 0.5 * noise_estimate / np.sqrt(len(x_observed))
        
        # Store current state
        history.append({
            'iteration': i + 1,
            'x_observed': x_observed.copy(),
            'y_observed': y_observed.copy(),
            'mu_estimate': mu_estimate,
            'noise_estimate': noise_estimate,
            'uncertainty': uncertainty,
            'conf_lower': mu_estimate - 1.96 * uncertainty,
            'conf_upper': mu_estimate + 1.96 * uncertainty
        })
        
        # Print progress
        if (i+1) % 5 == 0 or i == n_iterations - 1:
            print(f"Iteration {i+1}/{n_iterations}: "
                  f"Estimated center = {mu_estimate:.6f} +/- {uncertainty:.6f}, "
                  f"Noise estimate = {noise_estimate:.4f}")
        
        # Plot if this iteration is in the plot list
        if plot and (i+1) in plot_iterations:
            plot_idx = plot_iterations.index(i+1)
            if plot_idx < len(axs):
                plot_iteration_state(axs[plot_idx], history[i+1], i+1)
    
    # Final estimate with more robust settings for confidence
    final_mu = peak_center_mle(x_observed, y_observed, 0.7)
    final_uncertainty = 0.5 * noise_estimate / np.sqrt(len(x_observed))
    
    # Calculate the maximum intensity at the estimated center
    ml.DCM_PIEZO.move(final_mu, wait=True)
    max_intensity = measure_intensity(final_mu)
    
    print("\nFinal Pitch Optimization Results:")
    print(f"Optimal Pitch Position = {final_mu:.6f} +/- {final_uncertainty:.6f}")
    print(f"95% Confidence Interval: [{final_mu - 1.96*final_uncertainty:.6f}, {final_mu + 1.96*final_uncertainty:.6f}]")
    print(f"Maximum Intensity = {max_intensity:.4e}")
    print(f"Function evaluations: {len(x_observed)}")
    
    # Save and show the figure
    if plot and len(plot_iterations) > 0:
        plt.tight_layout()
        plt.savefig("pitch_optimization_iterations.png", dpi=150)
        plt.show()
    
    # Final convergence plot
    if plot:
        plot_convergence(history)
    
    # Restore original settings
    dl.ioni13.put('rawData.SCAN', scanmode_old)
    dl.ioni13.put('averFlt', averagemode_old)
    
    # Return results
    return {
        'optimal_pitch': final_mu,
        'uncertainty': final_uncertainty,
        'max_intensity': max_intensity,
        'x_observed': x_observed,
        'y_observed': y_observed,
        'history': history
    }

# Simple wrapper function for easy calling
def checkpitch():
    """
    Simple wrapper function for the Bayesian pitch optimization.
    Equivalent to the original checkpitch() but using Bayesian optimization.
    
    Usage:
    import checkpitchbayes as cpb
    cpb.checkpitch()
    """
    
    
    print('checkpitch (Bayesian optimization)')
    while(float(epics.caget('K6485:miocb0113rawData.PACT')) > 0):
        sleep(0.1)
    
    intensitystart = dl.ioni13.get('.VAL')
    # Run with sensible defaults
    results = physics_informed_pitch_optimization(
        n_iterations=20,  # 10 iterations is usually sufficient
        bounds=None,      # Use current position ±0.01
        plot=False,        # Generate plots
        plot_iterations=[20]  # Only plot the final iteration
    )
    
    # Move to the optimal position (already done in physics_informed_pitch_optimization)
    optimal_pitch = results['optimal_pitch']
    max_intensity = results['max_intensity']
    
    print(f"Optimization complete!")
    print(f"Optimal pitch position: {optimal_pitch:.6f}")
    print(f"Maximum intensity: {max_intensity:.4e}")
    while(float(epics.caget('K6485:miocb0113rawData.PACT')) > 0):
        sleep(0.1)
    
    intensitystop = dl.ioni13.get('.VAL')
    if intensitystop  <= 0.8* intensitystart:
        print('Repeat Pitch')
        checkpitch()
    return 0#;results

# Run the optimization if script is executed directly
if __name__ == "__main__":
    print("Running Bayesian Pitch Optimization")
    
    # Run with default settings
    results = physics_informed_pitch_optimization(
        n_iterations=20,  # Fewer iterations to save time
        plot=True,
        plot_iterations=[5, 10]
    )
    
    # Move to the optimal position
    ml.DCM_PIEZO.move(results['optimal_pitch'], wait=True)
    
    # Plot final results
    plt.figure(figsize=(10, 6))
    plt.plot(results['x_observed'], results['y_observed'], 'ko', label='Observations')
    plt.axvline(x=results['optimal_pitch'], color='g', linestyle='-', label='Optimal Pitch')
    plt.title('Pitch Optimization Results')
    plt.xlabel('Pitch Position')
    plt.ylabel('Intensity')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig("pitch_optimization_final.png", dpi=150)
    plt.show()
