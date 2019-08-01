import React from "react";
import {changePlaylistTrackPosition, playlistChanged, PlaylistItem} from "./api";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import List from '@material-ui/core/List';
import {arrayMove, SortableContainer, SortableElement, SortEnd, SortEvent} from 'react-sortable-hoc';
import PlaylistEntry from "./PlaylistEntry";

interface ContextState {
    playlistItems: PlaylistItem[];
    playlistTrackUrls: ReadonlySet<string>;
}

interface ContextProps {}

const INITIAL_CONTEXT_STATE: ContextState = { playlistItems: [], playlistTrackUrls: new Set() };

const PlaylistContext = React.createContext<ContextState>(INITIAL_CONTEXT_STATE);


class PlaylistContextProvider extends React.Component<ContextProps,ContextState> {

    constructor(props: ContextProps) {
        super(props);
        this.state = INITIAL_CONTEXT_STATE;
    }

    componentDidMount() {
        playlistChanged(this.setPlaylist);
    }

    setPlaylist = (items: PlaylistItem[]) => {
        this.setState({
            playlistItems: items,
            playlistTrackUrls: new Set(items.map(item => item.track.url)),
        });
    };

    render() {
        return (
            <PlaylistContext.Provider value={ {
                playlistItems: this.state.playlistItems,
                playlistTrackUrls: this.state.playlistTrackUrls,
            }}>
                {this.props.children}
            </PlaylistContext.Provider>
        );
    }
}

export {PlaylistContext, PlaylistContextProvider}

interface State {
    playlistItems: PlaylistItem[];
}

const styles = (theme: Theme) => createStyles({
    list: {
        overflow: 'auto'
    }
});

interface Props extends WithStyles<typeof styles> {}

const SortableItem = SortableElement(({playlistItem, playlistIndex}: {playlistItem: PlaylistItem, playlistIndex: number}) =>{
    return(
        <PlaylistEntry playlistItem={playlistItem} playlistIndex={playlistIndex}/>
    );
});

const SortableList = SortableContainer(({playlistItems, classNames}: {playlistItems: PlaylistItem[], classNames: string}) => {
    return (

        <List dense className={classNames}>
            {playlistItems.map((value, index) => (
                <SortableItem key={`item-${index}`} index={index} playlistItem={value} playlistIndex={index} />
            ))}
        </List>

    );
});

class Playlist extends React.Component<Props, State> {

    constructor(props: Props) {
        super(props);
        this.setPlaylist = this.setPlaylist.bind(this);
        this.onSortEnd = this.onSortEnd.bind(this);

        this.state = {playlistItems: []};
    }

    componentDidMount() {
        playlistChanged(this.setPlaylist)
    }

    setPlaylist(data: PlaylistItem[]) {
        this.setState({playlistItems: data });
    }

    onSortEnd (sort: SortEnd, event: SortEvent){
        const movedEntry = this.state.playlistItems[sort.oldIndex];
        this.setState({
            playlistItems: arrayMove(this.state.playlistItems, sort.oldIndex, sort.newIndex),
        });
        changePlaylistTrackPosition(movedEntry.playlist_entry_id, sort.newIndex)
    };

    render() {
        const { classes } = this.props;

        return (
            <SortableList playlistItems={this.state.playlistItems}
                          classNames={classes.list}
                          onSortEnd={this.onSortEnd}
                          useDragHandle={true}
                          lockAxis={'y'} />
        );
    }
}
export default withStyles(styles) (Playlist);
