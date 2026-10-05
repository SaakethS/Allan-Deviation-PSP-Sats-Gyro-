# Gyroscope Allan deviation results

Source: gyro_log(1).csv, recorded using the ESP32 logger. Input gyro units are rad/s, as labeled by the firmware. This analysis assumes that firmware scaling is correct.

## Recording and method

- 3,228,364 samples over 8.9481 hours, with measured mean sample rate 100.2190 Hz.
- All values finite; no backward timestamps or gaps above 20 ms.
- Typical intervals range from 9.56 to 10.11 ms. The initial interval is 4.747 ms. The calculation treats the stream as uniformly sampled at the measured mean rate; timestamps are used to check timing and determine that rate.
- Primary analysis excludes the first 600 seconds as a conservative warm-up precaution, leaving 3,168,233 samples. This does not establish thermal equilibrium. Dotted curves show the full recording for comparison.
- No interpolation, smoothing, linear detrending, or outlier removal was applied to the samples used for Allan deviation. Subtracting a constant mean improves numerical precision and leaves Allan deviation unchanged.
- The overlapping estimator compares adjacent m-sample means at every possible sample offset: variance = mean((next_mean - previous_mean)^2)/2. Allan deviation is its square root; tau = m / sample_rate.
- Averaging times extend to 1,580.65 seconds, restricting the largest clusters to about 1/20 of the retained record. The many overlapping differences are correlated and are not independent measurements. Confidence intervals were not estimated; uncertainty increases at long averaging times.
- The implementation was checked against direct adjacent block averages on independent synthetic data.

## Results

| Axis | Angle random walk (rad/sqrt(s)) | Angle random walk (deg/sqrt(hour)) | Short-time fitted slope | Minimum Allan deviation (rad/s) | Time at minimum (s) | Provisional bias instability (deg/hour) |
|---|---:|---:|---:|---:|---:|---:|
| X | 5.42886e-5 | 0.1866 | -0.4898 | 1.08584e-5 | 76.86 | 3.37 |
| Y | 4.80213e-5 | 0.1651 | -0.4928 | 7.26453e-6 | 110.49 | 2.26 |
| Z | 5.34225e-5 | 0.1837 | -0.4876 | 9.07257e-6 | 97.90 | 2.82 |

Angle random walk N was fitted over 0.1–1 second using sigma(tau) = N/sqrt(tau), with the log slope fixed at -1/2. Separate free-slope regressions are close to -1/2, supporting this interpretation. To convert rad/sqrt(s) to deg/sqrt(hour), multiply by (180/pi)*60.

The provisional bias values are the observed Allan minima divided by sqrt(2*ln(2)/pi), approximately 0.664, then converted to deg/hour. A minimum is not sufficient to uniquely identify flicker noise. X and Y rise after narrow minima; Z has a broader flatter region. Slow changes in the mean rates are visible in gyro_drift.png. Temperature was not logged, so their cause cannot be established. These numbers describe this run and should not be treated as independently validated sensor specifications.

Using the whole recording changes the minimum Allan deviations by approximately +3.3% (X), +8.5% (Y), and -0.4% (Z), compared with excluding the first ten minutes.

The raw output is visibly quantized in approximately 0.00106526 rad/s increments (0.061 deg/s). These are estimates for the configured sensor, readout and logging chain; a different range or filter configuration may change them.

## Use in the MEKF

The estimated gyro white-noise strength is N = [5.42886e-5, 4.80213e-5, 5.34225e-5] rad/sqrt(s). For a simplified small-angle error model driven by independent white gyro noise, the direct attitude process-noise contribution over a filter interval dt is diag(N^2)*dt:

    diag([2.94725e-9, 2.30605e-9, 2.85396e-9]) * dt

This block has units rad^2. A complete MEKF uses the appropriate noise input matrix and discrete covariance integration, including attitude/bias coupling. Do not use the provisional bias instability numbers as a bias random-walk diffusion coefficient: those describe different noise processes. This analysis does not claim a rate-random-walk coefficient from the rising tails because deterministic or temperature-related drift could contribute.

The retained-record mean rates are [0.00777571, -0.000851881, -0.00345673] rad/s. They are observed mean offsets for this stationary run, not the bias-instability values or universal calibration constants.

## Files and rerunning

- allan_deviation.png / .pdf: log-log plot of all axes.
- gyro_drift.png: one-minute average rates showing slow changes.
- allan_deviation.csv: averaging time, cluster size, and per-axis overlapping Allan deviation in rad/s, both with warm-up excluded and for the full recording.
- summary.json: machine-readable parameters.
- analyze_allan.py: reproducible NumPy/Matplotlib analysis script. Run:

    python analyze_allan.py "gyro_log(1).csv" results

Requires NumPy and Matplotlib. The original 150 MB raw recording is not duplicated in these result files.

Method reference: MathWorks, Inertial Sensor Noise Analysis Using Allan Variance:
https://www.mathworks.com/help/nav/ug/inertial-sensor-noise-analysis-using-allan-variance.html
