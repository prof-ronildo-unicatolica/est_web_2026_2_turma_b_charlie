export default function HotelSkeleton({ count = 3 }) {
  return (
    <div className="row g-4">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="col-md-6 col-lg-4">
          <div className="card h-100 shadow-sm border-0 placeholder-glow" aria-hidden="true">
            <div
              className="placeholder bg-secondary w-100"
              style={{ height: '200px', borderTopLeftRadius: '0.375rem', borderTopRightRadius: '0.375rem' }}
            />
            <div className="card-body">
              <h5 className="card-title placeholder-glow mb-2">
                <span className="placeholder col-8 bg-primary"></span>
              </h5>
              <p className="card-text placeholder-glow mb-3">
                <span className="placeholder col-4 me-2 bg-secondary"></span>
                <span className="placeholder col-3 bg-warning"></span>
              </p>
              <div className="mb-3 d-flex gap-1">
                <span className="placeholder col-3 bg-light border"></span>
                <span className="placeholder col-3 bg-light border"></span>
                <span className="placeholder col-3 bg-light border"></span>
              </div>
              <hr />
              <div className="d-flex justify-content-between align-items-center mt-3">
                <span className="placeholder col-4 py-2 bg-success"></span>
                <span className="placeholder col-4 py-2 bg-primary"></span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
