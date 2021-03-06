import abc

import numpy as np

class DataProcessor(object):
    """Base class for all data processing elements.

    Methods
    -------
    process_frame(frame)
        Process a single frame and return the result.
    process_sequence(frames)
        Process a sequence of frames.

    Notes
    -----
    Subclasses only need to implement one of the process_frame or
    process_sequence methods.  The default implementation of the other
    method will use the implemented method to implement the required
    functionality.

    For example, if the desired processing can be applied to each
    frame of data independently, then it is sufficient to implement
    process_frame.  However, if there is some shared state across an
    entire sequence, or if output is not produced for all input frames
    (e.g. in a voice activity detector) it is probably simpler to
    implement process_sequence instead.

    See Also
    --------
    Source
    Pipeline
    """
    def process_frame(self, frame):
        """Process a single frame and return the result."""
        return self.process_sequence([frame]).next()

    def process_sequence(self, frames):
        """Process a sequence of frames.

        Returns a generator which succesively yields each processed frame.
        """
        for x in frames:
            yield self.process_frame(x)


class Source(object):
    """Generator that yields data for use by DataProcessors.

    This is distinguised from DataProcessor in that it takes no input.

    Methods
    -------
    toarray(frames)
        Return the data generated by passing frames through this
        pipeline as a numpy array.

    Notes
    -----
    Subclasses only need to implement the iterator protocol.

    See Also
    --------
    DataProcessor
    Pipeline
    AudioSource : Source that yields samples from an audio file
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __iter__(self):
        pass
    
    def toarray(self):
        """Return the data generated by this source as a numpy array."""
        return np.asarray([x for x in self])


class Pipeline(DataProcessor):
    """Chain of DataProcessors.

    Methods
    -------
    toarray()
        Return the data generated by this source as a numpy array.

    Attributes
    ----------
    dps : list of DataProcessor objects to chain together

    Example
    -------
    The following code creates a DataProcessor that first turns the
    input into a mono signal, then resamples it, and finally computes
    the RMS energy of the resampled signal:
    >>> featext = Pipeline(Mono(), Resample(ratio=0.5), RMS())
   
    See Also
    --------
    STFT : Short-time Fourier Transform DataProcessor constructed as a
           Pipeline of simpler elements
    """
    def __init__(self, *dps):
        self.dps = dps

    def __iter__(self):
        return self.process_sequence()

    def process_sequence(self, frames=None):
        """Process a sequence of frames.

        Returns a generator which succesively yields each processed
        frame.  If frames is None (the default), the first
        DataProcessor in the pipeline is assumed to be a Source which
        will generate input frames.
        """
        if frames is None:
            gen = self.dps[0]
            if issubclass(gen.__class__, Source):
                gen = iter(gen)
        else:
            gen = self.dps[0].process_sequence(frames)

        for dp in self.dps[1:]:
            gen = dp.process_sequence(gen)

        return gen

    def toarray(self, frames=None):
        """Return the data generated by this pipeline as a numpy array."""
        return np.asarray([x for x in self.process_sequence(frames)])
