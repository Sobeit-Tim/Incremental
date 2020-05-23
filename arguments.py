import argparse
# import deepspeed

def get_args():
    parser = argparse.ArgumentParser(description='iCarl2.0')
    parser.add_argument('--batch-size', type=int, default=128, metavar='N',
                        help='input batch size for training (default: 64)')
    parser.add_argument('--replay-batch-size', type=int, default=32, metavar='N',
                        help='input batch size for training (default: 64)')
    parser.add_argument('--lr', type=float, default=0.1, metavar='LR',
                        help='learning rate (default: 0.1. Note that lr is decayed by args.gamma parameter args.schedule ')
    parser.add_argument('--alpha', type=float, default=1, help='KD strength')
    parser.add_argument('--ratio', type=float, default=1/512, help='variance ratio')
    parser.add_argument('--beta', type=float, default=1e-4, help='CI and uniform penalty strength')
    parser.add_argument('--schedule', type=int, nargs='+', default=[40,80],
                        help='Decrease learning rate at these epochs.')
    parser.add_argument('--gammas', type=float, nargs='+', default=[0.1, 0.1],
                        help='LR is multiplied by gamma on schedule, number of gammas should be equal to schedule')
    parser.add_argument('--momentum', type=float, default=0.9, metavar='M',
                        help='SGD momentum (default: 0.9)')
    parser.add_argument('--seed', type=int, default=0,
                        help='Seeds values to be used; seed introduces randomness by changing order of classes')
#     parser.add_argument('--decay', type=float, default=0.003, help='Weight decay (L2 penalty).')
    parser.add_argument('--decay', type=float, default=0.0001, help='Weight decay (L2 penalty).')
    parser.add_argument('--step-size', type=int, default=100, help='How many classes to add in each increment')
    parser.add_argument('--memory-budget', type=int, default=20000,
                        help='How many images can we store at max. 0 will result in fine-tuning')
    parser.add_argument('--nepochs', type=int, default=100, help='Number of epochs for each increment')
    parser.add_argument('--workers', type=int, default=32, help='Number of workers in Dataloaders')
    parser.add_argument('--base-classes', type=int, default=100, help='Number of base classes')
    parser.add_argument('--sample', type=int, default=10, help='Number of samples in BNN')
    parser.add_argument('--factor', type=int, default=4, help='Number of samples in BNN')
    parser.add_argument('--date', type=str, default='', help='(default=%(default)s)')
    parser.add_argument('--cutmix', action='store_true', default=False, help='Use cutmix')
    parser.add_argument('--debug', type=int, default=1, help='Use debug')
    parser.add_argument('--benchmark', action='store_true', default=False, help='Use cudnn.benchmark')
    parser.add_argument('--KD', action='store_true', default=False, help='Use Knowledge distillation')
    parser.add_argument('--bin-sigmoid', action='store_true', default=False, help='Binary classification using sigmoid')
    parser.add_argument('--bin-softmax', action='store_true', default=False, help='Binary classification usign softmax')
    parser.add_argument('--prev-new', action='store_true', default=False, help='Use Prev/New head')
    parser.add_argument('--lr-change', action='store_true', default=False, help='Use lr change')
    parser.add_argument('--uniform-penalty', action='store_true', default=False, help='Use uniform penalty')
    parser.add_argument('--CI', action='store_true', default=False, help='Use Confidence Integrated loss')
    parser.add_argument('--rand-init', action='store_true', default=False, help='Use random init')
    parser.add_argument('--local_rank', type=int, default=-1,help='local rank passed from distributed launcher')
    parser.add_argument('--dataset', default='', type=str, required=True,
                        choices=['CIFAR10',
                                 'CIFAR100', 
                                 'Imagenet',
                                 'VggFace2_1K',
                                 'VggFace2_5K',
                                 'Google_Landmark_v2_1K',
                                 'Google_Landmark_v2_10K'], 
                        help='(default=%(default)s)')
    parser.add_argument('--ablation', default='None', type=str, required=False,
                        choices=['None', 
                                 'naive',], 
                        help='(default=%(default)s)')
    parser.add_argument('--loss', default='CE', type=str, required=False,
                        choices=['GCE', 
                                 'CE'], 
                        help='(default=%(default)s)')
    parser.add_argument('--trainer', default='', type=str, required=True,
                        choices=['lwf', 
                                 'er', 
                                 'coreset',
                                 'icarl', 
                                 'IL2M', 
                                 'bic', 
                                 'er_NMC', 
                                 'coreset_NMC'], 
                        help='(default=%(default)s)')

    parser.add_argument('--strategy', default='RingBuffer', type=str, required=False,
                        choices=['Reservior', 
                                 'RingBuffer',
                                 'Weighted'], 
                        help='(default=%(default)s)')
    
    
#     parser = deepspeed.add_config_arguments(parser)
    args=parser.parse_args()

    return args