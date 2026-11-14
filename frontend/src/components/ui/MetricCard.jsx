import { motion, useReducedMotion } from 'framer-motion';

export default function MetricCard({
  label,
  value,
  hint,
  trend,
  trendDir = 'up',
  icon: Icon,
  index = 0,
}) {
  const reduce = useReducedMotion();
  return (
    <motion.article
      className="card card-pad rw-metric-card"
      initial={reduce ? false : { opacity: 0, y: 12, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      whileHover={reduce ? undefined : { y: -3, transition: { duration: 0.18, ease: 'easeOut' } }}
      transition={{
        duration: 0.32,
        delay: index * 0.055,
        ease: [0.23, 1, 0.32, 1],
      }}
    >
      <div className="metric-label">
        <span>{label}</span>
        {Icon ? (
          <span className="rw-metric-icon">
            <Icon size={16} strokeWidth={1.85} />
          </span>
        ) : null}
      </div>
      <motion.p
        key={String(value)}
        initial={reduce ? false : { opacity: 0.4, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        className="metric-value"
      >
        {value}
      </motion.p>
      {trend ? <p className={`metric-trend ${trendDir}`}>{trend}</p> : null}
      {hint ? <p className="card-sub">{hint}</p> : null}
    </motion.article>
  );
}
